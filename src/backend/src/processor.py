from __future__ import annotations

import datetime as dt
import hashlib
import re
from typing import Optional

from src.backend.src.utils import date_to_str, clean_for_llm, resolve_sender_hint
from src.backend.src.outlook import read_emails_from_folder
from src.backend.src.classifier import score_email
from src.backend.src.llm import extract_views_from_batch
from src.backend.src.config.parameters import DEFAULT_LLM_PROVIDER, DEFAULT_LLM_MODEL
from src.backend.src.db.database import SessionLocal, initialize_database
from src.backend.src.db.models import Email, UnderlyingView


def ensure_db() -> None:
    initialize_database()


def build_email_hash(email_dict: dict) -> str:
    hash_input = f"{email_dict.get('subject', '')}{email_dict.get('sender', '')}{email_dict.get('received_time', '')}"
    return hashlib.md5(hash_input.encode()).hexdigest()


def parse_date_range(start_date: Optional[str], end_date: Optional[str]) -> tuple[str, str]:
    start_date_str = start_date or date_to_str(dt.date.today())
    end_date_str = end_date or date_to_str(dt.date.today())
    return start_date_str, end_date_str


def _coerce_confidence(value: object, default: int = 50) -> int:
    if value is None or isinstance(value, bool):
        return default

    if isinstance(value, (int, float)):
        confidence = int(round(float(value)))
    else:
        match = re.search(r"-?\d+(?:\.\d+)?", str(value))
        if not match:
            return default
        confidence = int(round(float(match.group())))

    return max(0, min(100, confidence))


def _resolve_provider_and_model(provider: Optional[str], model: Optional[str]) -> tuple[str, str]:
    resolved_model = model or DEFAULT_LLM_MODEL
    resolved_provider = provider

    if not resolved_provider:
        if resolved_model.startswith("gpt-") or resolved_model.startswith("o1-"):
            resolved_provider = "openai"
        elif resolved_model in ["mistral", "llama3:8b", "llama3"]:
            resolved_provider = "ollama"
        else:
            resolved_provider = DEFAULT_LLM_PROVIDER

    return resolved_provider, resolved_model


def _normalize_text_key(value: object, limit: int = 200) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip()).lower()
    return text[:limit]


def _view_signature(email_id: int, view: dict, bank_name: str) -> tuple[str, str, str, str, str]:
    return (
        str(email_id),
        str(view.get("underlying", "")).strip().upper(),
        str(view.get("sentiment", "")).strip().lower(),
        bank_name.strip().lower(),
        _normalize_text_key(view.get("levels", "")) or _normalize_text_key(view.get("rationale", "")),
    )


def _existing_view_signatures(db, email_id: int) -> set[tuple[str, str, str, str, str]]:
    signatures: set[tuple[str, str, str, str, str]] = set()
    for existing in db.query(UnderlyingView).filter(UnderlyingView.email_id == email_id).all():
        signatures.add(
            (
                str(email_id),
                (existing.underlying or "").strip().upper(),
                (existing.sentiment or "").strip().lower(),
                (existing.bank or "").strip().lower(),
                _normalize_text_key(existing.levels or "") or _normalize_text_key(existing.rationale or ""),
            )
        )
    return signatures


def _create_view(db, new_email: Email, view: object, seen_signatures: Optional[set[tuple[str, str, str, str, str]]] = None) -> bool:
    if not isinstance(view, dict):
        print(f"[WARN] Skipping non-dict view for email_id={new_email.id}: {view!r}")
        return False

    sender_hint = resolve_sender_hint(new_email.sender, new_email.body_summary or "")
    bank_name = str(view.get("bank") or sender_hint)
    if "@" in bank_name:
        bank_name = bank_name.split("@")[-1].split(".")[0].capitalize()

    signature = _view_signature(new_email.id, view, bank_name)
    if seen_signatures is not None and signature in seen_signatures:
        print(f"[INFO] Duplicate view skipped for email_id={new_email.id}: {view.get('underlying')} / {view.get('sentiment')}")
        return False

    new_view = UnderlyingView(
        email_id=new_email.id,
        underlying=str(view.get("underlying", "")).upper()[:15],
        sentiment=str(view.get("sentiment", "")).lower()[:20],
        bank=bank_name[:30],
        date=new_email.received_time.date() if new_email.received_time else dt.date.today(),
        rationale=str(view.get("rationale", "")),
        levels=str(view.get("levels", "")),
        confidence=_coerce_confidence(view.get("confidence", 50))
    )
    db.add(new_view)
    if seen_signatures is not None:
        seen_signatures.add(signature)
    return True


def _extract_views_for_saved_emails(
    db,
    saved_emails: list[dict],
    provider: str,
    model: str,
) -> int:
    views_created = 0
    if not saved_emails:
        return views_created

    batch_data = [
        {
            "id": email_info["email"].id,
            "body": email_info["cleaned_body"],
            "sender": email_info.get("sender_hint") or resolve_sender_hint(email_info["email"].sender, email_info["cleaned_body"]),
        }
        for email_info in saved_emails
    ]
    views_batch = extract_views_from_batch(batch_data, provider=provider, model=model)
    print(f"[DEBUG] Parsed views_batch length={len(views_batch) if views_batch is not None else 'None'}")

    if views_batch is not None:
        if len(views_batch) == len(saved_emails):
            for email_info, views_data in zip(saved_emails, views_batch):
                new_email = email_info["email"]
                seen_signatures = _existing_view_signatures(db, new_email.id)
                if views_data:
                    for view in views_data:
                        if _create_view(db, new_email, view, seen_signatures=seen_signatures):
                            views_created += 1
        elif len(views_batch) == 1 and len(saved_emails) > 1:
            print("[WARN] LLM returned a single email view list for multiple emails; assigning all views to the first saved email.")
            new_email = saved_emails[0]["email"]
            seen_signatures = _existing_view_signatures(db, new_email.id)
            for view in views_batch[0]:
                if _create_view(db, new_email, view, seen_signatures=seen_signatures):
                    views_created += 1
        else:
            print(f"[WARN] Unexpected views_batch format or count: expected {len(saved_emails)}, got {len(views_batch)}")
            print("[WARN] Could not safely map the batch to emails; no ambiguous view will be inserted.")
        db.commit()

    return views_created


def _query_emails_missing_views(db, start_date_str: str, end_date_str: str) -> list[Email]:
    start_dt = dt.datetime.fromisoformat(start_date_str)
    end_dt = dt.datetime.fromisoformat(end_date_str).replace(hour=23, minute=59, second=59)

    return (
        db.query(Email)
        .outerjoin(UnderlyingView, UnderlyingView.email_id == Email.id)
        .filter(Email.received_time >= start_dt, Email.received_time <= end_dt)
        .filter(UnderlyingView.id.is_(None))
        .order_by(Email.received_time.asc(), Email.id.asc())
        .all()
    )


def process_email_range(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    refresh: bool = False,
    strict: bool = False
) -> dict:
    start_date_str, end_date_str = parse_date_range(start_date, end_date)
    provider, model = _resolve_provider_and_model(provider, model)

    print(f"[*] Processing range {start_date_str} to {end_date_str} with provider={provider} model={model} strict={strict}")
    ensure_db()
    db = SessionLocal()

    if refresh:
        start_dt = dt.datetime.fromisoformat(start_date_str)
        end_dt = dt.datetime.fromisoformat(end_date_str).replace(hour=23, minute=59, second=59)
        db.query(UnderlyingView).filter(UnderlyingView.date >= start_dt.date(), UnderlyingView.date <= end_dt.date()).delete()
        db.query(Email).filter(Email.received_time >= start_dt, Email.received_time <= end_dt).delete()
        db.commit()

    emails_raw = read_emails_from_folder(start_date=start_date_str, end_date=end_date_str)

    new_valid_emails = []
    saved_emails = []
    reprocessed_emails = 0

    for email_dict in emails_raw:
        sender_hint = resolve_sender_hint(
            email_dict.get("sender", email_dict.get("from", "")),
            email_dict.get("body", ""),
        )
        scored_email = dict(email_dict)
        scored_email["sender_hint"] = sender_hint

        df_one = score_email(scored_email)
    
        if df_one is None or df_one.is_empty() :

            print(f"[-] Filtered email (no score): {email_dict.get('subject', 'no subject')}")
            continue
        
        row = df_one.to_dicts()[0]
        reasons = row.get("reasons", [])
        keep = bool(row.get("keep_for_step3"))

        if keep and strict and row.get("label") == "market_commentary":
            market_signals = sum(1 for sig in ["fx", "index_macro_ticker", "direction", "flows", "macro_calendar"] if sig in reasons)
            if market_signals < 2 or len(reasons) < 3:
                keep = False
                reasons.append("strict_filter")

        if keep:
            md5_hash = build_email_hash(email_dict)
            existing = db.query(Email).filter(Email.md5_hash == md5_hash).first()
        
            if existing:
                has_views = db.query(UnderlyingView.id).filter(UnderlyingView.email_id == existing.id).first() is not None
                if not has_views:
                    cleaned_body = existing.body_summary or clean_for_llm(email_dict.get("body", ""))
                    saved_emails.append({"email": existing, "cleaned_body": cleaned_body, "sender_hint": sender_hint})
                    reprocessed_emails += 1
                    print(f"[~] Re-queued saved email without views: {existing.subject}")
            else:
                email_dict["md5_hash"] = md5_hash
                email_dict["sender_hint"] = sender_hint
                new_valid_emails.append(email_dict)
                print(f"[+] Kept email: {email_dict.get('subject', 'no subject')} - label: {row.get('label')} - reasons: {reasons}")
        else :

            print(f"[-] Filtered email: {email_dict.get('subject', 'no subject')} - label: {row.get('label')} - reasons: {reasons}")

    for item in new_valid_emails:
        cleaned_body = clean_for_llm(item.get("body", ""))
        new_email = Email(
            md5_hash=item["md5_hash"],
            sender=item.get("sender_hint") or item.get("sender", item.get("from", "")),
            subject=item.get("subject", ""),
            received_time=item.get("received_time"),
            body_summary=cleaned_body
        )
        db.add(new_email)
        db.commit()
        db.refresh(new_email)
        saved_emails.append({"email": new_email, "cleaned_body": cleaned_body, "sender_hint": item.get("sender_hint")})

    views_created = _extract_views_for_saved_emails(db, saved_emails, provider, model)

    db.close()
    return {
        "status": "completed",
        "provider": provider,
        "model": model,
        "start_date": start_date_str,
        "end_date": end_date_str,
        "emails_found": len(emails_raw),
        "new_emails": len(new_valid_emails),
        "emails_reprocessed": reprocessed_emails,
        "emails_sent_to_llm": len(saved_emails),
        "views_created": views_created,
        "refresh": refresh
    }


def backfill_missing_views(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> dict:
    start_date_str, end_date_str = parse_date_range(start_date, end_date)
    provider, model = _resolve_provider_and_model(provider, model)

    print(f"[*] Backfilling missing views from DB for range {start_date_str} to {end_date_str} with provider={provider} model={model}")
    ensure_db()
    db = SessionLocal()

    emails_missing_views = _query_emails_missing_views(db, start_date_str, end_date_str)
    saved_emails = [
        {
            "email": email,
            "cleaned_body": email.body_summary or "",
            "sender_hint": resolve_sender_hint(email.sender, email.body_summary or ""),
        }
        for email in emails_missing_views
        if email.body_summary
    ]

    views_created = _extract_views_for_saved_emails(db, saved_emails, provider, model)
    db.close()

    return {
        "status": "completed",
        "provider": provider,
        "model": model,
        "start_date": start_date_str,
        "end_date": end_date_str,
        "emails_found": len(emails_missing_views),
        "emails_reprocessed": len(saved_emails),
        "views_created": views_created,
        "source": "database_backfill",
    }

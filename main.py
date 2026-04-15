from __future__ import annotations

import os
from dotenv import load_dotenv
load_dotenv()

import datetime as dt
from src.utils import date_to_str, clean_for_llm
from src.outlook import read_emails_from_folder
from src.classifier import score_email
from src.llm import extract_views_from_text
from src.config.parameters import DEFAULT_LLM_PROVIDER, DEFAULT_LLM_MODEL
from src.db.database import SessionLocal, engine
from src.db.models import Base, Email, UnderlyingView
import argparse

def main() -> None :

    parser = argparse.ArgumentParser(description="Extract market views from Outlook emails using an LLM.")
    
    parser.add_argument("--start-date", type=str, default=None, help="Start date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--end-date", type=str, default=None, help="End date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--provider", type=str, default=None, help="LLM Provider (openai or ollama)")
    parser.add_argument("--model", type=str, default=None, help="LLM model name. Inferred by provider if omitted.")
    
    args = parser.parse_args()

    # Default missing dates to today
    start_date_str = args.start_date or date_to_str(dt.date.today())
    end_date_str = args.end_date or date_to_str(dt.date.today())

    # Dynamic model and provider resolution
    model = args.model or DEFAULT_LLM_MODEL
    provider = args.provider
    
    if not provider :

        if model.startswith("gpt-") or model.startswith("o1-"):
            provider = "openai"
        
        elif model in ["mistral", "llama3:8b", "llama3"]:
            provider = "ollama"
        
        else:
            provider = DEFAULT_LLM_PROVIDER

    # Initialize the DB schema if it doesn't exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print(f"\n[*] Reading emails from Outlook (Start: {start_date_str}, End: {end_date_str})...")
    
    # Fetch based on parsed arguments
    emails_raw = read_emails_from_folder(start_date=start_date_str, end_date=end_date_str)
    print(f"\n[*] Found {len(emails_raw)} emails total in this timeframe.")

    new_valid_emails = []

    print("[*] Running Stage 1 Classifier Filter...")
    
    for email_dict in emails_raw:
    
        # Step 1: Logically filter noise using existing fast classifier
        df_one = score_email(email_dict)
    
        if df_one is None or df_one.is_empty():
            continue
            
        row = df_one.to_dicts()[0]
        # Only keep interesting emails that passed the strict quality gating
        if row.get("keep_for_step3") is True:
            received_time = email_dict.get("received_time")
            sender = email_dict.get("sender", email_dict.get("from", ""))
            
            # Prevent duplicate processing by checking DB
            existing = db.query(Email).filter(
                Email.received_time == received_time,
                Email.sender == sender
            ).first()
            
            if not existing:
                new_valid_emails.append(email_dict)

    print(f"[*] Kept {len(new_valid_emails)} NEW emails after Stage 1 filter.")

    if not new_valid_emails:
        print("[*] No new relevant emails. Exiting.")
        db.close()
        return

    # Process kept emails with LLM
    print("[*] Running Stage 2 LLM Extraction...")
    for idx, item in enumerate(new_valid_emails, 1):
        body = item.get("body", "")
        # Clean the email body to save tokens and improve extraction accuracy
        cleaned_body = clean_for_llm(body)
        
        # Save email metadata
        new_email = Email(
            sender=item.get("sender", item.get("from", "")),
            subject=item.get("subject", ""),
            received_time=item.get("received_time"),
            body_summary=cleaned_body
        )
        db.add(new_email)
        db.commit()
        db.refresh(new_email)
        
        print(f"[{idx}/{len(new_valid_emails)}] Extracting views for Email ID {new_email.id}: {new_email.subject[:50]}...")
        
        # Send to LLM with dynamic provider
        views_data = extract_views_from_text(cleaned_body, provider=provider, model=model)
        
        if views_data is None:
            print("    --> LLM extraction failed (e.g., API key missing or connection error). Reverting database save so this email can be retried later.")
            db.delete(new_email)
            db.commit()
            continue

        if views_data :
            print(f"    --> Found {len(views_data)} views!")
            for view in views_data:
                # Fallback to sender if model didn't extract the bank explicitly
                bank_name = str(view.get("bank") or new_email.sender)
                if "@" in bank_name:
                    # Simplify domain to bank name heuristics if it's an email address
                    bank_name = bank_name.split("@")[-1].split(".")[0].capitalize()

                new_view = UnderlyingView(
                    email_id=new_email.id,
                    underlying=str(view.get("underlying", "")).upper()[:15], # clamp string lengths just in case
                    sentiment=str(view.get("sentiment", "")).lower()[:20],
                    bank=bank_name[:30],
                    date=new_email.received_time.date() if new_email.received_time else dt.date.today(),
                    rationale=str(view.get("rationale", "")),
                    levels=str(view.get("levels", "")),
                    confidence=int(view.get("confidence", 50))  # New: save confidence
                )
                db.add(new_view)
            db.commit()
        else:
            print(f"    --> No views extracted.")

    print("[*] Pipeline completed successfully.")
    db.close()

if __name__ == "__main__":
    main()
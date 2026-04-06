from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

import polars as pl

from src.config.parameters import (
    MARKET_KEYWORDS, MARKET_PHRASES, DIRECTIONAL_WORDS,
    CAUSAL_MARKERS, MACRO_EVENTS, PRODUCT_OFFER_WORDS,
    ADMIN_NOISE_WORDS, RE_FX_PAIR_SLASH, RE_FX_PAIR_JOIN,
    RE_INDEX, RE_CONTEXT_LEVEL, RE_FX_DECIMAL, RE_PERCENT_BPS,
    RE_TICKER, CAPS_STOPLIST, FOOTER_CUT_PATTERNS,
    # --- new imports ---
    RESEARCH_KEYWORDS, RESEARCH_PHRASES, BANK_RESEARCH_DOMAINS,
    RESEARCH_HARD_BLOCKERS, RE_RESEARCH_SUBJECT, RE_PRICE_TARGET,
    RE_EPS_ESTIMATE,
)


def _safe_str(x: Any) -> str:
    return "" if x is None else str(x)


def strip_footer(raw: str, min_chars: int = 800) -> str:
    """
    Safe footer stripper:
    - only cuts if the footer marker appears AFTER min_chars
    - prevents cutting the header (e.g. "Not a product of MS Research" on line 1)
    """
    if not raw:
        return ""
    low = raw.lower()
    cut = len(raw)

    for pat in FOOTER_CUT_PATTERNS:
        m = re.search(pat, low)
        if m and m.start() >= min_chars:
            cut = min(cut, m.start())

    return raw[:cut].strip()


def _contains_any(text_low: str, words: set[str]) -> bool:
    return any(w in text_low for w in words)


def _count_weighted_hits(text_low: str, weights: Dict[str, int]) -> int:
    total = 0
    for w, k in weights.items():
        if " " in w or "-" in w:
            if w in text_low:
                total += k
        else:
            if re.search(rf"\b{re.escape(w)}\b", text_low):
                total += k
    return total


def _extract_tickers(raw_text: str) -> List[str]:
    if not raw_text:
        return []
    cands = RE_TICKER.findall(raw_text)
    out: List[str] = []
    for c in cands:
        if c in CAPS_STOPLIST:
            continue
        out.append(c)
    return sorted(set(out))


def _count_levels(text_raw: str) -> int:
    """
    Count only meaningful market "levels":
      - contextual (support/resistance/target/above/below...) + number near it
      - FX-style decimals (1.18 / 1.0850 / 1.1856)
    """
    ctx = RE_CONTEXT_LEVEL.findall(text_raw)
    fx = RE_FX_DECIMAL.findall(text_raw)
    return len(ctx) + len(fx)


def _detect_research_signals(
    subject_raw: str,
    text_low: str,
    text_raw: str,
    sender: str,
) -> Tuple[int, List[str], Dict[str, bool]]:
    """
    Dedicated detector for bank research emails.

    Returns:
        research_score  – additive score contribution (can be negative)
        research_reasons – list of string tags explaining the score
        flags            – dict of boolean signals for downstream logic
    """
    rscore = 0
    rreasons: List[str] = []

    # --- Hard blockers: kill research label outright ---
    has_hard_block = _contains_any(text_low, RESEARCH_HARD_BLOCKERS)
    if has_hard_block:
        return -20, ["research_hard_blocked"], {
            "has_research_keyword": False,
            "has_research_phrase": False,
            "has_price_target": False,
            "has_eps_estimate": False,
            "has_bank_sender": False,
            "has_research_subject": False,
            "has_hard_block": True,
        }

    # --- Keyword scoring ---
    kw_score = _count_weighted_hits(text_low, RESEARCH_KEYWORDS)
    if kw_score > 0:
        rscore += kw_score
        rreasons.append(f"research_keywords:{kw_score}")

    # --- Phrase scoring ---
    phrase_score = 0
    matched_phrases: List[str] = []
    for phrase, w in RESEARCH_PHRASES.items():
        if phrase in text_low:
            phrase_score += w
            matched_phrases.append(phrase)
    if phrase_score > 0:
        rscore += phrase_score
        rreasons.append(f"research_phrases:{phrase_score}")

    # --- Structural signals ---
    has_price_target = bool(RE_PRICE_TARGET.search(text_raw))
    if has_price_target:
        rscore += 6
        rreasons.append("price_target_pattern")

    has_eps_estimate = bool(RE_EPS_ESTIMATE.search(text_raw))
    if has_eps_estimate:
        rscore += 3
        rreasons.append("eps_estimate_pattern")

    # --- Subject line signal (very high signal-to-noise) ---
    has_research_subject = bool(RE_RESEARCH_SUBJECT.search(subject_raw))
    if has_research_subject:
        rscore += 8
        rreasons.append("research_subject_line")

    # --- Sender domain signal ---
    sender_low = sender.lower()
    has_bank_sender = any(domain in sender_low for domain in BANK_RESEARCH_DOMAINS)
    if has_bank_sender:
        rscore += 5
        rreasons.append("bank_sender_domain")

    # --- Structural length heuristic: real research notes tend to be long ---
    body_len = len(text_raw)
    if body_len > 2000:
        rscore += 2
        rreasons.append("long_research_body")

    flags = {
        "has_research_keyword": kw_score > 0,
        "has_research_phrase": phrase_score > 0,
        "has_price_target": has_price_target,
        "has_eps_estimate": has_eps_estimate,
        "has_bank_sender": has_bank_sender,
        "has_research_subject": has_research_subject,
        "has_hard_block": False,
    }
    return rscore, rreasons, flags


def score_email(email_dict: Optional[Dict[str, Any]] = None) -> pl.DataFrame:
    """
    Step 1 classifier (no AI).

    Labels:
      - bank_research       : formal research note / analyst report from a bank
      - market_commentary   : sales/trading colour, morning notes, macro commentary
      - trade_offer         : structured product / pricing sheet
      - admin_noise         : ops, KYC, meetings, invoices
      - unknown             : catch-all

    keep_for_step3 is True for bank_research AND market_commentary emails
    that pass their respective quality gates.
    """
    if not email_dict:
        return pl.DataFrame([{
            "score": 0,
            "label": "unknown",
            "keep_for_step3": False,
            "reasons": ["empty"],
        }])

    subject_raw = _safe_str(email_dict.get("subject"))
    body_raw    = _safe_str(email_dict.get("body"))
    sender      = _safe_str(email_dict.get("sender", email_dict.get("from", "")))

    # Strip footer (very important)
    body_core = strip_footer(body_raw)
    text_raw  = f"{subject_raw}\n{body_core}"
    text_low  = text_raw.lower()

    reasons: List[str] = []
    score = 0

    # ------------------------------------------------------------------ #
    #  BLOCKERS                                                            #
    # ------------------------------------------------------------------ #
    has_product_offer = _contains_any(text_low, PRODUCT_OFFER_WORDS)
    has_admin_noise   = _contains_any(text_low, ADMIN_NOISE_WORDS)

    if has_product_offer:
        score -= 8
        reasons.append("product_offer")

    if has_admin_noise:
        score -= 8
        reasons.append("admin_noise")

    # ------------------------------------------------------------------ #
    #  MARKET COMMENTARY scoring (unchanged logic)                        #
    # ------------------------------------------------------------------ #
    market_kw_score = _count_weighted_hits(text_low, MARKET_KEYWORDS)
    score += market_kw_score
    if market_kw_score > 0:
        reasons.append(f"market_keywords:{market_kw_score}")

    for phrase, w in MARKET_PHRASES.items():
        if phrase in text_low:
            score += w
            reasons.append(f"phrase:{phrase}")

    has_fx    = bool(RE_FX_PAIR_SLASH.search(text_raw)) or bool(RE_FX_PAIR_JOIN.search(text_low))
    has_index = bool(RE_INDEX.search(text_raw))
    has_assets = has_fx or has_index

    if has_fx:
        score += 4
        reasons.append("fx")
    if has_index:
        score += 2
        reasons.append("index_macro_ticker")

    has_direction = any(re.search(rf"\b{re.escape(w)}\b", text_low) for w in DIRECTIONAL_WORDS)
    has_causal    = any(m in text_low for m in CAUSAL_MARKERS)
    has_macro     = any(re.search(rf"\b{re.escape(w)}\b", text_low) for w in MACRO_EVENTS)
    has_flows     = any(k in text_low for k in (
        "positioning", "flows", "unwind", "cta", "real money", "deleveraging", "momentum"
    ))

    if has_direction:
        score += 2
        reasons.append("direction")
    if has_causal:
        score += 2
        reasons.append("causal")
    if has_flows:
        score += 2
        reasons.append("flows")
    if has_macro:
        score += 1
        reasons.append("macro_calendar")

    levels_count = _count_levels(text_raw)
    if levels_count >= 2:
        score += 2
        reasons.append(f"levels:{levels_count}")

    if RE_PERCENT_BPS.search(text_raw):
        score += 1
        reasons.append("percent_bps")

    tickers = _extract_tickers(subject_raw + "\n" + body_core)
    if has_assets and tickers:
        score += min(3, 1 + len(tickers) // 3)
        reasons.append(f"tickers:{len(tickers)}")

    if len(body_core) > 600:
        score += 1
        reasons.append("long_body")

    # ------------------------------------------------------------------ #
    #  BANK RESEARCH scoring (new)                                        #
    # ------------------------------------------------------------------ #
    research_score, research_reasons, research_flags = _detect_research_signals(
        subject_raw, text_low, text_raw, sender
    )
    reasons.extend(research_reasons)

    # Research score feeds into the global score
    score += research_score

    # Clamp
    score = int(max(-25, min(40, score)))  # ceiling raised to 40 to accommodate research

    # ------------------------------------------------------------------ #
    #  LABEL DECISION                                                      #
    # ------------------------------------------------------------------ #

    # Hard admin/noise check (highest priority)
    if has_admin_noise and score < 3:
        label = "admin_noise"

    # Bank research: requires strong evidence, no hard blocks
    elif (
        not research_flags["has_hard_block"]
        and research_score >= 10                          # meaningful research evidence
        and (
            research_flags["has_research_subject"]
            or research_flags["has_price_target"]
            or (research_flags["has_research_keyword"] and research_flags["has_research_phrase"])
            or (research_flags["has_bank_sender"] and research_flags["has_research_keyword"])
        )
    ):
        label = "bank_research"

    # Trade offer: product language without research or causal market narrative
    elif has_product_offer and not (has_causal or has_flows or has_macro or research_score >= 5):
        label = "trade_offer"

    # Market commentary: clear market structure
    elif has_assets or has_macro or has_flows or has_causal:
        label = "market_commentary"

    else:
        label = "unknown"

    # ------------------------------------------------------------------ #
    #  STEP-3 GATE                                                         #
    # ------------------------------------------------------------------ #

    # Bank research gate: need at least 2 independent research signals
    research_signal_count = sum([
        research_flags["has_research_subject"],
        research_flags["has_price_target"],
        research_flags["has_eps_estimate"],
        research_flags["has_research_phrase"],
        research_flags["has_bank_sender"],
        research_flags["has_research_keyword"] and research_score >= 8,
    ])

    # Market commentary gate (unchanged): need ≥2 of assets/causal/flows/direction/macro
    market_signal_count = sum([has_assets, has_causal, has_flows, has_direction, has_macro])

    keep_for_step3 = bool(
        (label == "bank_research"      and research_signal_count >= 2)
        or
        (label == "market_commentary"  and market_signal_count >= 2)
    )

    # ------------------------------------------------------------------ #
    #  OUTPUT                                                              #
    # ------------------------------------------------------------------ #
    out = dict(email_dict)
    out.update({
        "label":             label,
        "keep_for_step3":    keep_for_step3,
        "score":             score,
        "reasons":           reasons,
        "tickers":           tickers,
        "fx_present":        has_fx,
        "index_present":     has_index,
        "levels_count":      levels_count,
        "body_core_len":     len(body_core),
        # research-specific fields
        "research_score":    research_score,
        "research_signals":  research_signal_count,
        "has_price_target":  research_flags["has_price_target"],
        "has_eps_estimate":  research_flags["has_eps_estimate"],
        "has_bank_sender":   research_flags["has_bank_sender"],
    })

    # IMPORTANT: 1-row dataframe
    return pl.DataFrame([out])
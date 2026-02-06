from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import polars as pl

from src.config.parameters import (
    MARKET_KEYWORDS, MARKET_PHRASES, DIRECTIONAL_WORDS, 
    CAUSAL_MARKERS, MACRO_EVENTS, PRODUCT_OFFER_WORDS,
    ADMIN_NOISE_WORDS, RE_FX_PAIR_SLASH, RE_FX_PAIR_JOIN,
    RE_INDEX, RE_CONTEXT_LEVEL, RE_FX_DECIMAL, RE_PERCENT_BPS,
    RE_TICKER, CAPS_STOPLIST, FOOTER_CUT_PATTERNS
)


def _safe_str(x: Any) -> str :
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



def _contains_any (text_low: str, words: set[str]) -> bool :
    """
    Docstring for _contains_any
    
    :param text_low: Description
    :type text_low: str
    :param words: Description
    :type words: set[str]
    :return: Description
    :rtype: bool
    """
    return any(w in text_low for w in words)


def _count_weighted_hits (text_low: str, weights: Dict[str, int]) -> int :
    """
    Docstring for _count_weighted_hits
    
    :param text_low: Description
    :type text_low: str
    :param weights: Description
    :type weights: Dict[str, int]
    :return: Description
    :rtype: int
    """
    total = 0
    
    for w, k in weights.items() :
        
        # word boundary for single words; substring for multi-word phrases
        if " " in w or "-" in w :
            
            if w in text_low:
                total += k
        
        else :

            if re.search(rf"\b{re.escape(w)}\b", text_low):
                total += k
    
    return total


def _extract_tickers(raw_text: str) -> List[str] :
    """
    Docstring for _extract_tickers
    
    :param raw_text: Description
    :type raw_text: str
    :return: Description
    :rtype: List[str]
    """
    if not raw_text :
        return []
    
    cands = RE_TICKER.findall(raw_text)
    out: List[str] = []
    
    for c in cands :

        if c in CAPS_STOPLIST:
            continue
        
        # keep only 2-5 caps tokens
        out.append(c)

    return sorted(set(out))


def _count_levels(text_raw: str) -> int :
    """
    Count only meaningful market "levels":
      - contextual (support/resistance/target/above/below...) + number near it
      - FX-style decimals (1.18 / 1.0850 / 1.1856)
    """
    ctx = RE_CONTEXT_LEVEL.findall(text_raw)
    fx = RE_FX_DECIMAL.findall(text_raw)

    return len(ctx) + len(fx)


def score_email(email_dict: Optional[Dict[str, Any]] = None) -> pl.DataFrame:
    """
    Step 1 classifier (no AI).
    Output contains:
      - label: market_commentary / trade_offer / admin_noise / unknown
      - keep_for_step3: strict filter for your project (FX & Equities positioning)
      - score: ranking inside the kept set
    """
    if not email_dict :

        return pl.DataFrame([{"score": 0, "label": "unknown", "keep_for_step3": False, "reasons": ["empty"]}])

    subject_raw = _safe_str(email_dict.get("subject"))
    body_raw = _safe_str(email_dict.get("body"))

    # Strip footer (very important)
    body_core = strip_footer(body_raw)
    text_raw = f"{subject_raw}\n{body_core}"
    text_low = text_raw.lower()

    reasons: List[str] = []
    score = 0

    # --- Blockers (not necessarily reject, but strong signals) ---
    has_product_offer = _contains_any(text_low, PRODUCT_OFFER_WORDS)
    has_admin_noise = _contains_any(text_low, ADMIN_NOISE_WORDS)

    if has_product_offer :

        score -= 8
        reasons.append("product_offer")
    
    if has_admin_noise :
        
        score -= 8
        reasons.append("admin_noise")

    # --- Market evidence scoring ---
    score += _count_weighted_hits(text_low, MARKET_KEYWORDS)
    
    if score > 0 :
        reasons.append("market_keywords")

    for phrase, w in MARKET_PHRASES.items() :

        if phrase in text_low :

            score += w
            reasons.append(f"phrase:{phrase}")

    # Assets presence
    has_fx = bool(RE_FX_PAIR_SLASH.search(text_raw)) or bool(RE_FX_PAIR_JOIN.search(text_low))
    
    has_index = bool(RE_INDEX.search(text_raw))
    has_assets = has_fx or has_index

    if has_fx :

        score += 4
        reasons.append("fx")
    
    if has_index :

        score += 2
        reasons.append("index_macro_ticker")

    # Directional + causal + flows + macro events (for gating)
    has_direction = any(re.search(rf"\b{re.escape(w)}\b", text_low) for w in DIRECTIONAL_WORDS)
    has_causal = any(m in text_low for m in CAUSAL_MARKERS)
    has_macro = any(re.search(rf"\b{re.escape(w)}\b", text_low) for w in MACRO_EVENTS)

    # crude "flows" already in MARKET_KEYWORDS (positioning/flows/unwind/cta...), but keep a strong reason:
    has_flows = any(k in text_low for k in ("positioning", "flows", "unwind", "cta", "real money", "deleveraging", "momentum"))

    if has_direction :

        score += 2
        reasons.append("direction")
    
    if has_causal :

        score += 2
        reasons.append("causal")
    
    if has_flows :

        score += 2
        reasons.append("flows")
    
    if has_macro :

        score += 1
        reasons.append("macro_calendar")

    # Levels (meaningful only)
    levels_count = _count_levels(text_raw)
    if levels_count >= 2:
        score += 2
        reasons.append(f"levels:{levels_count}")

    # Percent/bps often appears in market commentary
    if RE_PERCENT_BPS.search(text_raw):
        score += 1
        reasons.append("percent_bps")

    # Tickers: only count if market context exists
    tickers = _extract_tickers(subject_raw + "\n" + body_core)
    if has_assets and tickers:
        score += min(3, 1 + len(tickers) // 3)
        reasons.append(f"tickers:{len(tickers)}")

    # Length helps a bit (after footer strip)
    if len(body_core) > 600:
        score += 1
        reasons.append("long_body")

    # Clamp
    score = int(max(-25, min(25, score)))

    # --- Label decision ---
    if has_product_offer and not (has_causal or has_flows or has_macro):
        label = "trade_offer"
    elif has_admin_noise and score < 3:
        label = "admin_noise"
    else:
        # if it has clear market structure, we keep label market_commentary even if it includes some "trade idea"
        label = "market_commentary" if (has_assets or has_macro or has_flows or has_causal) else "unknown"

    # --- STRICT Step3 gate for YOUR project (FX & Equities positioning) ---
    # Need at least 2 of: assets / causal / flows / direction / macro
    gate = sum([has_assets, has_causal, has_flows, has_direction, has_macro]) >= 2

    # Also block pure offer/admin
    keep_for_step3 = bool(gate and (label == "market_commentary"))

    out = dict(email_dict)
    out.update(
        {
            "label": label,
            "keep_for_step3": keep_for_step3,
            "score": score,
            "reasons": reasons,
            "tickers": tickers,
            "fx_present": has_fx,
            "index_present": has_index,
            "levels_count": levels_count,
            "body_core_len": len(body_core),
        }
    )

    # IMPORTANT: 1-row dataframe
    return pl.DataFrame([out])

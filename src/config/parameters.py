from __future__ import annotations

import os
import re
from dotenv import load_dotenv

load_dotenv()

EMAILBOX_SUFFIX = os.getenv("EMAILBOX_SUFFIX")

# -------------- MARKET signals --------------

# Words that indicate "market view / positioning / flows / narrative"
MARKET_KEYWORDS = {

    "market" : 1, "commentary" : 2, "macro" : 2, "strategy" : 2,
    "outlook" : 2, "positioning" : 3, "position": 1, "flows": 3,
    "flow": 2, "unwind": 3, "deleveraging": 3, "cta": 2, "real money": 3,
    "risk-on": 2, "risk off": 2, "risk-off": 2, "momentum": 2, "vol": 1,
    "volatility": 2, "skew": 2, "gamma": 2, "hedge" : 2, "earnings" : 1,
    "inflation" : 2, "rates" : 2, "yield" : 2, "yields" : 2, "auction" : 2,
    "cuts": 2, "hike" : 2, "hikes" : 2, "dovish" : 2, "hawkish" : 2, "support": 2,
    "resistance": 2, "target": 2, "above" : 1, "below" : 1, "break" : 1, "range": 1,

}

# Strong phrases
MARKET_PHRASES = {

    "market focus" : 3, "we expect" : 4, "our view" : 3,
    "position unwind" : 4, "stretched positioning": 4,
    "risk premium" : 3, "momentum trade" : 3, "cross-asset" : 3,

}
MARKET_PHRASES.update({
    "sales and trading commentary": 6,
    "morning note": 5,
    "market commentary": 5,
})



# Directional language (useful for gating)
DIRECTIONAL_WORDS = {

    "bullish", "bearish", "neutral", "upside", "downside",
    "supported", "pressured", "sell-off", "rally", "slump", "correction",
    "in the red", "in the green"

}

# Causal / narrative markers (VERY IMPORTANT for "trend" emails)
CAUSAL_MARKERS = {

    "because", "due to", "driven by", "amid", "following", "as", "catalyzed", "catalyst",
    "reflects", "which means", "as a result"

}

# Macro calendar terms
MACRO_EVENTS = {

    "nfp", "cpi", "pmi", "ism", "fomc", "ecb", "boe", "boj", "central bank",
    "payrolls", "unemployment", "inflation", "manufacturing"

}


# -------------- BLOCKERS (exclude from Step3) --------------

# Product / offer / structured / pricing content (NOT your project scope)
PRODUCT_OFFER_WORDS = {

    "autocall", "note", "reoffer", "maturity", "coupon", "barrier",
    "knock-out", "knock out", "ko", "termsheet", "indicative", "refresh", "pricing",
    "observation", "strike", "final terms", "preliminary terms",

}

# Admin/ops noise
ADMIN_NOISE_WORDS = {

    "invoice", "payment", "settlement", "kyc", "aml", "onboarding", "docusign",
    "meeting", "invitation", "teams", "webinar",
    "unsubscribe", "noreply", "no-reply", "support", "ticket",
    "error export", "iddsupport", "salesforce"

}


# -------------- Regex patterns --------------

# FX pair like EUR/USD, USDJPY shown either with slash or concatenated.
RE_FX_PAIR_SLASH = re.compile(r"\b[A-Z]{3}\/[A-Z]{3}\b")
RE_FX_PAIR_JOIN  = re.compile(r"\b(?:EURUSD|USDJPY|GBPUSD|AUDUSD|USDCAD|USDCHF|NZDUSD|USDCNH|USDZAR)\b", re.IGNORECASE)

# Equity index / macro tickers
RE_INDEX = re.compile(r"\b(?:SPX|NDX|RTY|INDU|DXY|VIX|MOVE|UST|JGB|BUND|GILT)\b")

# "levels" only when contextual or FX-like decimal
RE_CONTEXT_LEVEL = re.compile(r"\b(support|resistance|target|above|below|break|range)\b.{0,25}\b(\d+(?:\.\d+)?)\b", re.IGNORECASE)
RE_FX_DECIMAL    = re.compile(r"\b\d\.\d{2,5}\b")  # 1.18 / 1.1856 / 1.0850

# % and bps
RE_PERCENT_BPS = re.compile(r"\b\d{1,3}(?:\.\d+)?\s*%|\b\d+(?:\.\d+)?\s*(?:bp|bps)\b", re.IGNORECASE)

# crude ticker candidates (will be filtered by stoplist + gating)
RE_TICKER = re.compile(r"\b[A-Z]{2,5}\b")

CAPS_STOPLIST = {

    "US","EU","UK","USD","EUR","GBP","JPY","CPI","PMI","NFP","ISM","FOMC","ECB","BOE","BOJ",
    "RE","FW","FWD","THE","AND","FOR","ONLY","AM","PM","II","SAM","VAT","DATE","XML",
    "APAC","EMEA","EMFX","DM","GM","NAV"

}


# -------------- Footer stripping patterns --------------

FOOTER_CUT_PATTERNS = [

    r"\bimportant information\b",
    r"\bimportant disclosures\b",
    r"\bimportant information and qualifications\b",
    r"\bqualifications\b",
    r"\bdisclosures\b",
    r"\bconflict of interest\b",
    r"\bnon-reliance\b",
    r"\bnot a fiduciary\b",
    r"\bterms of business\b",
    r"\bprivacy\b",
    r"\bunsubscribe\b",
    r"\bif you are not the intended recipient\b",
    r"\bthe information contained in this electronic message\b",
    r"\bcopyright\b",

]

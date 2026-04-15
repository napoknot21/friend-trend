from __future__ import annotations

import os
import re
from dotenv import load_dotenv

load_dotenv()

EMAILBOX_SUFFIX = os.getenv("EMAILBOX_SUFFIX")

# -------------- PROCESS SETTINGS --------------
DEFAULT_LOOKBACK_DAYS = 30
DEFAULT_LLM_PROVIDER = "openai"  # Default to remote OpenAI
DEFAULT_LLM_MODEL = "gpt-4o-mini"  # Default OpenAI model
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

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


# -------------- BANK RESEARCH signals (new) --------------

# Words strongly associated with formal bank research reports
RESEARCH_KEYWORDS = {

    # Analyst actions
    "initiate": 4, "initiating": 4, "coverage": 3, "upgrade": 4, "downgrade": 4,
    "reiterate": 3, "reiterating": 3, "maintain": 2, "maintained": 2,

    # Rating language
    "overweight": 4, "underweight": 4, "equalweight": 4, "equal-weight": 4,
    "outperform": 4, "underperform": 4, "neutral": 2, "buy": 2, "sell": 2, "hold": 2,

    # Research artifacts
    "price target": 5, "pt": 1, "eps": 3, "ebitda": 3, "revenue": 2,
    "forecast": 3, "estimate": 2, "estimates": 2, "consensus": 3,
    "valuation": 3, "multiple": 2, "pe ratio": 3, "p/e": 3,
    "dcf": 3, "sum-of-parts": 3, "sotp": 3, "nav": 2,

    # Report structural cues
    "analyst": 4, "equity research": 5, "fixed income research": 5,
    "research note": 5, "research report": 5, "sector": 2, "industry": 2,
    "company note": 4, "flash note": 4, "result note": 4, "preview": 3, "review": 2,
    "deep dive": 3, "thematic": 3, "thesis": 3,

    # Quantitative / financial modeling language
    "margin": 2, "free cash flow": 3, "fcf": 3, "capex": 2, "leverage": 2,
    "debt": 1, "equity": 2, "net income": 2, "beat": 2, "miss": 2, "in line": 2,

}

# Strong multi-word research phrases
RESEARCH_PHRASES = {

    "we initiate": 6,
    "initiating coverage": 6,
    "we upgrade": 6,
    "we downgrade": 6,
    "price target of": 5,
    "price target to": 5,
    "raise our price target": 6,
    "lower our price target": 6,
    "increase our target": 5,
    "cut our target": 5,
    "earnings per share": 4,
    "we reiterate": 5,
    "our rating": 4,
    "12-month target": 5,
    "12 month target": 5,
    "base case": 3,
    "bull case": 3,
    "bear case": 3,
    "risk/reward": 3,
    "risk reward": 3,
    "key risks": 3,
    "investment thesis": 5,
    "investment case": 5,
    "see upside": 4,
    "see downside": 4,
    "we see": 3,
    "we believe": 3,
    "we think": 3,
    "in our view": 4,
    "from a valuation": 4,
    "at current levels": 3,
    "relative to peers": 3,
    "peer group": 3,
    "sector view": 4,
    "top pick": 4,
    "high conviction": 4,
    "catalyst watch": 4,

}

# Known bank/research sender domain fragments — used to boost score
BANK_RESEARCH_DOMAINS = {

    "goldmansachs", "gs.com",
    "jpmorgan", "jpmchase",
    "morganstanley", "ms.com",
    "barclays",
    "deutschebank", "db.com",
    "citigroup", "citi.com",
    "ubs.com",
    "bnpparibas", "bnp.com",
    "societegenerale", "sgcib",
    "hsbc.com",
    "bofa", "bofasecurities", "ml.com",
    "credit-suisse", "creditsuisse",
    "wellsfargo",
    "macquarie",
    "jefferies",
    "rbc.com", "rbccm",
    "td.com", "tdsecurities",
    "nomura",
    "mizuho",
    "stifel",
    "baird.com",
    "berenberg",
    "piper",
    "cowen",
    "evercore",
    "lazard",
    "rothschild",

}

# Subject-line patterns that strongly suggest a research email
RE_RESEARCH_SUBJECT = re.compile(
    r"\b(initiating|initiation|upgrade|downgrade|overweight|underweight|outperform|"
    r"underperform|price target|equity research|company note|flash note|result note|"
    r"sector note|thematic|deep.?dive|preview|review)\b",
    re.IGNORECASE,
)

# Pattern for explicit price targets in body: "$42", "CHF 120", "EUR 85.00"
RE_PRICE_TARGET = re.compile(
    r"(?:price\s+target|target\s+price|pt)[^\d]{0,10}(?:[A-Z]{1,3}\s*)?\d+(?:\.\d{1,2})?",
    re.IGNORECASE,
)

# EPS / consensus estimate patterns  "EPS of $2.10", "FY25E EPS"
RE_EPS_ESTIMATE = re.compile(
    r"\b(?:eps|ebitda|revenue|sales)\s*(?:of|est\.?|e|forecast)?\s*[\$€£]?\s*\d+(?:\.\d+)?",
    re.IGNORECASE,
)


# -------------- BLOCKERS (exclude from Step3) --------------

# Product / offer / structured / pricing content (NOT your project scope)
PRODUCT_OFFER_WORDS = {

    "autocall", "reoffer", "maturity", "coupon", "barrier",
    "knock-out", "knock out", "ko", "termsheet", "indicative", "refresh",
    "observation", "strike", "final terms", "preliminary terms",
    "trade recap", "trade confirmation", "affirmation", "confirmation notice",
    "monthly transparency", "transparency figures", "statement summary",
    "statement of collateral holdings", "navs", "preconfirmation", "pre-confirmation",
    "option expiries", "position summary", "position update",
    # note: removed generic "note" and "pricing" — too many false-positives
    # (research notes use "note", earnings have "pricing power")

}

# Admin/ops noise
ADMIN_NOISE_WORDS = {

    "invoice", "payment", "settlement", "kyc", "aml", "onboarding", "docusign",
    "meeting invitation", "teams meeting", "webinar invitation",
    "unsubscribe", "noreply", "no-reply", "support ticket",
    "error export", "iddsupport", "salesforce",
    "calendar invite", "conference call dial",
    "trade recap", "monthly transparency", "transparency figures",
    "trade confirmation", "affirmation", "confirmation notice",
    "statement summary", "statement of collateral holdings", "navs",
    "account name mismatch", "preconfirmation", "pre-confirmation",
    "heroics global strategy sicav-raif", "positions 14042026",
    "regulatory vm margin summary", "option expiries", "confirmation notice",
    "please affirm", "trade confirmation", "opening disregard notice",

}

# Words that kill a research label even if research keywords score high
RESEARCH_HARD_BLOCKERS = {

    "termsheet", "final terms", "preliminary terms", "reoffer", "autocall",
    "knock-out", "invoice", "payment due", "kyc required",
    "trade recap", "trade confirmation", "affirmation", "confirmation notice",
    "monthly transparency", "transparency figures", "statement summary",
    "statement of collateral holdings", "account name mismatch",
    "please affirm", "option expiries", "opening disregard notice",

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
    r"\banalyst certification\b",
    r"\bregulatory disclosures\b",
    r"\bthis report has been prepared by\b",
    r"\bthis communication is for informational purposes\b",

]
from __future__ import annotations

import re
import os

from dotenv import load_dotenv

load_dotenv()

EMAILBOX_SUFFIX = os.getenv("EMAILBOX_SUFFIX")

DIRECTIONAL_WORDS = [

    "bullish", "bearish", "neutral",
    "long", "short", "buy", "sell",
    "overweight", "underweight",
    "risk-on", "risk-off",
    "support", "resistance", "target",
    "positioning", "flows", "cta", "real money"

]

NOISE_WORDS = [

    "invoice", "payment", "settlement",
    "kyc", "aml", "onboarding",
    "webinar", "invitation", "unsubscribe",
    "attached", "attachment", "document"

]

FX_PAIR = re.compile(r"\b[A-Z]{3}\/[A-Z]{3}\b")
LEVELS  = re.compile(r"\b\d{1,5}(?:\.\d+)?\b")

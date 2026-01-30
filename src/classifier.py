from __future__ import annotations

import polars as pl

from typing import List, Tuple, Dict, Optional

from src.config.parameters import NOISE_WORDS, DIRECTIONAL_WORDS, FX_PAIR, LEVELS


def score_email (email_dict : Dict[str, str] = None) -> Tuple[int, List[str]] :
    """
    Docstring for score_email
    
    :param subject: Description
    :type subject: str
    :param body: Description
    :type body: str
    :return: Description
    :rtype: Tuple[int, List[str]]
    """
    if email_dict is None :
        return None
    
    if email_dict.get("subject", None) is None or email_dict.get("body", None) is None :
        return None
    
    subject =  email_dict.get("subject")
    body =  email_dict.get("body")

    text = f"{subject}\n{body}"
    low = text.lower()

    score = 0
    reasons = []

    noise_hits = sum(1 for w in NOISE_WORDS if w in low)

    if noise_hits :

        score -= 3
        reasons.append("noise")

    dir_hits = sum(1 for w in DIRECTIONAL_WORDS if w in low)

    if dir_hits :

        score += 2
        reasons.append("directional_language")

    if FX_PAIR.search(text) :

        score += 2
        reasons.append("fx_pair")

    if len(LEVELS.findall(text)) >= 2 :

        score += 2
        reasons.append("price_levels")

    if len(body) < 80 :

        score -= 1
        reasons.append("short_body")


    email_dict.update(
        {
            "score" : score,
            "reasons" : reasons
        }
    )

    df = pl.DataFrame(email_dict)

    return df
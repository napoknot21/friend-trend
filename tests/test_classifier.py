from __future__ import annotations

import unittest

from src.backend.src.classifier import score_email
from src.backend.src.utils import resolve_sender_hint


class ClassifierFilteringTests(unittest.TestCase):
    def test_internal_heroics_morning_brief_is_not_kept(self) -> None:
        email = {
            "subject": "Heroics Capital - Morning Brief - 16/04/2026",
            "sender": "alexandre.tramini@heroics-capital.com",
            "body": """
Heroics Capital Morning Brief - 16/04/2026

Aux Etats-Unis, le S&P 500 (SPX) monte de 0.8% et le Nasdaq 100 (NDX) progresse de 1.4%.
USD/JPY recule because softer CPI keeps the market focused on rate cuts.
Support sits near 1.0850 and resistance near 1.0950.
""",
        }

        row = score_email(email).to_dicts()[0]

        self.assertEqual(row["label"], "internal_digest")
        self.assertFalse(row["keep_for_step3"])
        self.assertTrue(row["is_internal_digest"])
        self.assertIn("internal_digest", row["reasons"])

    def test_forwarded_citi_morning_note_keeps_bank_sender_signal(self) -> None:
        body = """
www.heroics-capital.com

De : Bourgeon, Thomas <thomas.bourgeon@citi.com>
Envoye : jeudi 16 avril 2026 08:57
Sujet : CitiFX Morning Note

Market Commentary, Intended for Institutional Clients Only
SPX pushes to fresh highs because positioning remains supportive after softer CPI.
USD/JPY is pressured while EUR/USD support stands near 1.0850.
"""
        email = {
            "subject": "TR : CitiFX Morning Note: SPX extends rally after CPI",
            "sender": "alexandre.tramini@heroics-capital.com",
            "body": body,
        }

        row = score_email(email).to_dicts()[0]

        self.assertEqual(resolve_sender_hint(email["sender"], body), "thomas.bourgeon@citi.com")
        self.assertEqual(row["sender_hint"], "thomas.bourgeon@citi.com")
        self.assertEqual(row["label"], "market_commentary")
        self.assertTrue(row["keep_for_step3"])
        self.assertTrue(row["has_bank_sender"])


if __name__ == "__main__":
    unittest.main()

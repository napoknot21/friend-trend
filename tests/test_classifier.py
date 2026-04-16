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

    def test_isda_virtual_conference_is_filtered_as_admin_noise(self) -> None:
        email = {
            "subject": "Advanced equity derivatives - In depth training, Online, May 19",
            "sender": "conferences@isda.org",
            "body": """
Watch live or catch the replay
Agenda
Register

This is an ISDA Virtual Conference.
Educational credits are available and programme topics include variable share forwards.
""",
        }

        row = score_email(email).to_dicts()[0]

        self.assertEqual(row["label"], "admin_noise")
        self.assertFalse(row["keep_for_step3"])
        self.assertTrue(row["has_admin_sender"])
        self.assertTrue(row["has_event_marketing"])

    def test_internal_confirmation_mailbox_is_filtered_even_with_fx_terms(self) -> None:
        email = {
            "subject": "RE: EURNOK Settlement",
            "sender": "confirmations@heroics-capital.com",
            "body": """
Hello Charlotte,

We would also like to invest some of our cash in MMFs.
Therefore, could you please provide information regarding transaction costs.

Best,
Heroics Confirmations
""",
        }

        row = score_email(email).to_dicts()[0]

        self.assertEqual(row["label"], "admin_noise")
        self.assertFalse(row["keep_for_step3"])
        self.assertTrue(row["has_admin_sender"])
        self.assertFalse(row["has_admin_hard_block"])

    def test_collateral_margin_summary_is_filtered(self) -> None:
        email = {
            "subject": "IMVM MSESE HEROICS GLOBAL STRATEGY SICAV RAIF HEROICS VOLATILITY *OTC OPTIONS* / 15-Apr-2026",
            "sender": "Emea.Collateral@morganstanley.com",
            "body": """
Attached is a summary of Morgan Stanley's current exposures to you arising out of transactions between us.
The margin requirements relating to transactions covered in this report may differ significantly from pricing.
Contact: EMEA Collateral
""",
        }

        row = score_email(email).to_dicts()[0]

        self.assertEqual(row["label"], "admin_noise")
        self.assertFalse(row["keep_for_step3"])
        self.assertTrue(row["has_admin_sender"])
        self.assertTrue(row["has_admin_hard_block"])

    def test_bank_ops_option_email_does_not_trigger_price_target_false_positive(self) -> None:
        email = {
            "subject": "ALTARIUS ASSET MANAGEMENT FX OPTION VD 16/04/2026",
            "sender": "Vivek.Yadav@morganstanley.com",
            "body": """
Hi Team,

Please agree with below option and SSI.
MS PAY EUR 4,051.19 @ UBSWDEFFXXX / DE66501306000513900013

Thanks,
Vivek Yadav, on behalf of Morgan Stanley Firmwide Ops
""",
        }

        row = score_email(email).to_dicts()[0]

        self.assertEqual(row["label"], "admin_noise")
        self.assertFalse(row["keep_for_step3"])
        self.assertFalse(row["has_price_target"])
        self.assertTrue(row["has_admin_hard_block"])


if __name__ == "__main__":
    unittest.main()

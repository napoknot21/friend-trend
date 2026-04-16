from __future__ import annotations

import unittest

from src.backend.src.llm import _batch_prompt, _extract_json_payload, _single_email_prompt, normalize_batch_result
from src.backend.src.processor import _coerce_confidence, _normalize_text_key, _view_signature


class LlmNormalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.emails_data = [
            {"id": 10, "body": "A"},
            {"id": 11, "body": "B"},
            {"id": 12, "body": "C"},
        ]

    def test_aligns_views_by_email_id_and_fills_missing_emails(self) -> None:
        raw_result = {
            "views": [
                {"email_id": 12, "views": [{"underlying": "SPX"}]},
                {"email_id": 10, "views": [{"underlying": "EURUSD"}]},
            ]
        }

        normalized = normalize_batch_result(raw_result, self.emails_data)

        self.assertEqual(
            normalized,
            [
                [{"underlying": "EURUSD"}],
                [],
                [{"underlying": "SPX"}],
            ],
        )

    def test_aligns_dict_keyed_by_email_id(self) -> None:
        raw_result = {
            "views": {
                "10": [{"underlying": "EURUSD"}],
                "12": [{"underlying": "SPX"}],
            }
        }

        normalized = normalize_batch_result(raw_result, self.emails_data)

        self.assertEqual(
            normalized,
            [
                [{"underlying": "EURUSD"}],
                [],
                [{"underlying": "SPX"}],
            ],
        )

    def test_extracts_json_inside_markdown_code_block(self) -> None:
        payload = """```json
        {"views":[{"email_id":10,"views":[{"underlying":"EURUSD"}]}]}
        ```"""

        extracted = _extract_json_payload(payload)

        self.assertEqual(
            extracted,
            {"views": [{"email_id": 10, "views": [{"underlying": "EURUSD"}]}]},
        )

    def test_prompts_explicitly_require_multiple_underlyings(self) -> None:
        batch_prompt = _batch_prompt("Email 1 ...")
        single_prompt = _single_email_prompt("Body ...")

        self.assertIn("If one email mentions several underlyings, return several view objects", batch_prompt)
        self.assertIn("If the email mentions several underlyings, return several view objects", single_prompt)
        self.assertIn('Only use a generic label like "EQUITIES" or "FX"', batch_prompt)


class ProcessorHelperTests(unittest.TestCase):
    def test_coerce_confidence_handles_percent_strings_and_bounds(self) -> None:
        self.assertEqual(_coerce_confidence("85%"), 85)
        self.assertEqual(_coerce_confidence("101"), 100)
        self.assertEqual(_coerce_confidence(-5), 0)
        self.assertEqual(_coerce_confidence(None), 50)
        self.assertEqual(_coerce_confidence("high conviction"), 50)

    def test_view_signature_normalizes_whitespace_and_case(self) -> None:
        view = {
            "underlying": "spx",
            "sentiment": "Bullish",
            "levels": " 6100 target ",
            "rationale": "ignored when levels present",
        }

        signature = _view_signature(7, view, "Morgan Stanley")

        self.assertEqual(signature, ("7", "SPX", "bullish", "morgan stanley", "6100 target"))
        self.assertEqual(_normalize_text_key("  A   lot \n of \t spaces "), "a lot of spaces")


if __name__ == "__main__":
    unittest.main()

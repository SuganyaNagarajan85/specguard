"""Tests for documentation claim extraction."""

from __future__ import annotations

import unittest

from specguard.extractor import extract_claims_regex


class ExtractorTests(unittest.TestCase):
    def test_extracts_key_value_and_table_claims(self) -> None:
        markdown = "\n".join(
            [
                "Retries: 3",
                "",
                "| Setting | Value |",
                "| --- | --- |",
                "| Timeout | 5 |",
            ]
        )

        claims = extract_claims_regex(markdown)
        values = {(claim["key"], claim["value"], claim["line"]) for claim in claims}

        self.assertIn(("retries", 3, 1), values)
        self.assertIn(("timeout", 5, 5), values)

    def test_extracts_simple_natural_language_claims(self) -> None:
        markdown = "The retry count defaults to 4 before a request fails."

        claims = extract_claims_regex(markdown)

        self.assertEqual(claims[0]["key"], "retries")
        self.assertEqual(claims[0]["value"], 4)


if __name__ == "__main__":
    unittest.main()

"""Tests for result comparison and reporting."""

from __future__ import annotations

import unittest

from specguard.comparator import compare_claims_to_code
from specguard.reporter import COMMENT_MARKER, format_github_comment


class ComparatorAndReporterTests(unittest.TestCase):
    def test_matches_alias_keys_and_preserves_locations(self) -> None:
        claims = [
            {
                "key": "retries",
                "value": 3,
                "text": "Retries: 3",
                "line": 2,
                "source_file": "docs.md",
            }
        ]
        constants = {
            "retry_count": {
                "value": 2,
                "source_file": "config.py",
                "line": 8,
                "context": "RETRY_COUNT = 2",
            }
        }

        comparison = compare_claims_to_code(claims, constants)
        mismatch = comparison["mismatches"][0]

        self.assertEqual(mismatch["matched_code_key"], "retry_count")
        self.assertEqual(mismatch["doc_line"], 2)
        self.assertEqual(mismatch["code_line"], 8)

    def test_github_comment_contains_stable_marker(self) -> None:
        results = {
            "mismatches": [
                {
                    "key": "retries",
                    "doc_value": 3,
                    "code_value": 2,
                    "doc_file": "docs.md",
                    "doc_line": 1,
                    "code_file": "config.py",
                    "code_line": 4,
                    "ai_verdict": {"status": "incorrect", "confidence": 92, "reason": "Mismatch"},
                }
            ]
        }

        comment = format_github_comment(results)

        self.assertIn(COMMENT_MARKER, comment)
        self.assertIn("docs.md:1", comment)
        self.assertIn("config.py:4", comment)


if __name__ == "__main__":
    unittest.main()

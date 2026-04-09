"""Tests for Python configuration extraction."""

from __future__ import annotations

import tempfile
from pathlib import Path
import textwrap
import unittest

from specguard.code_parser import parse_python_file


class CodeParserTests(unittest.TestCase):
    def test_extracts_richer_configuration_patterns(self) -> None:
        source = textwrap.dedent(
            """
            import os
            from dataclasses import dataclass

            RETRIES: int = 2
            SETTINGS = {"timeout": 5}
            FEATURE_ENABLED = os.getenv("FEATURE_ENABLED", True)

            @dataclass
            class AppConfig:
                retries: int = 7
                timeout: int = 9
            """
        ).strip()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.py"
            path.write_text(source, encoding="utf-8")

            constants = parse_python_file(path)

        self.assertEqual(constants["retries"]["value"], 7)
        self.assertEqual(constants["timeout"]["value"], 9)
        self.assertEqual(constants["feature_enabled"]["value"], True)


if __name__ == "__main__":
    unittest.main()

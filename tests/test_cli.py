"""Tests for SpecGuard CLI behavior."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


class CliTests(unittest.TestCase):
    def test_cli_exits_non_zero_when_drift_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            doc_path = root / "sample.md"
            code_path = root / "sample.py"
            report_path = root / "report.md"

            doc_path.write_text("Retries: 3\n", encoding="utf-8")
            code_path.write_text("RETRIES = 2\n", encoding="utf-8")

            process = subprocess.run(
                [
                    sys.executable,
                    "cli.py",
                    "--doc",
                    str(doc_path),
                    "--code",
                    str(code_path),
                    "--github-output",
                    str(report_path),
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(process.returncode, 1)
            self.assertIn("SpecGuard detected documentation drift", process.stdout)
            self.assertTrue(report_path.exists())


if __name__ == "__main__":
    unittest.main()

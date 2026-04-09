"""Command-line interface for SpecGuard."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from specguard.reporter import format_cli_report, format_github_comment
from specguard.scanner import scan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Detect documentation drift between docs and code.")
    parser.add_argument("--doc", required=True, help="Path to the markdown documentation file.")
    parser.add_argument("--code", required=True, help="Path to a Python file or directory to scan.")
    parser.add_argument(
        "--use-llm-extraction",
        action="store_true",
        help="Use OpenAI as a fallback extractor when regex extraction finds no claims.",
    )
    parser.add_argument(
        "--github-output",
        help="Optional path to write a GitHub markdown report.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    results = scan(args.doc, args.code, use_llm_extraction=args.use_llm_extraction)
    cli_output = format_cli_report(results)
    print(cli_output)

    if args.github_output:
        Path(args.github_output).write_text(format_github_comment(results), encoding="utf-8")

    return 1 if results["has_drift"] else 0


if __name__ == "__main__":
    sys.exit(main())

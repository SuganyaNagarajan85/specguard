"""Format SpecGuard results for terminals and GitHub PR comments."""

from __future__ import annotations

from pathlib import Path
from typing import Any


COMMENT_MARKER = "<!-- specguard-report -->"


def _location(file_path: str | None, line_number: int | None) -> str:
    if not file_path:
        return "unknown location"
    name = Path(file_path).name
    return f"{name}:{line_number}" if line_number else name


def _format_mismatch(mismatch: dict[str, Any], markdown: bool = False) -> str:
    verdict = mismatch.get("ai_verdict", {})
    status = str(verdict.get("status", "uncertain")).capitalize()
    confidence = verdict.get("confidence", 0)
    reason = verdict.get("reason", "No reason provided.")
    doc_location = _location(mismatch.get("doc_file"), mismatch.get("doc_line"))
    code_location = _location(mismatch.get("code_file"), mismatch.get("code_line"))

    return (
        f"- {mismatch['key']} mismatch:\n"
        f"  Doc: {mismatch['doc_value']} ({doc_location})\n"
        f"  Code: {mismatch['code_value']} ({code_location})\n"
        f"  AI Verdict: {status} (Confidence: {confidence}%)\n"
        f"  Reason: {reason}"
    )


def format_cli_report(results: dict[str, Any]) -> str:
    """Render a human-readable CLI report."""
    if not results["mismatches"]:
        return "SpecGuard found no documentation drift."

    lines = ["SpecGuard detected documentation drift:"]
    for mismatch in results["mismatches"]:
        lines.append("")
        lines.append(_format_mismatch(mismatch))
    return "\n".join(lines)


def format_github_comment(results: dict[str, Any]) -> str:
    """Render a markdown report suitable for GitHub pull request comments."""
    if not results["mismatches"]:
        return f"{COMMENT_MARKER}\n## SpecGuard Report\n\nNo documentation drift detected."

    lines = [
        COMMENT_MARKER,
        "## SpecGuard Report",
        "",
        "⚠️ SpecGuard detected documentation drift:",
        "",
    ]
    for mismatch in results["mismatches"]:
        lines.append(_format_mismatch(mismatch, markdown=True))
        lines.append("")
    return "\n".join(lines).rstrip()

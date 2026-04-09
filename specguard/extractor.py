"""Extract structured claims from markdown documentation."""

from __future__ import annotations

import json
import re
from typing import Any

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - dependency may be absent in some environments
    OpenAI = None


LINE_CLAIM_PATTERN = re.compile(
    r"^\s*[-*]?\s*(?P<key>[a-zA-Z][\w\s-]{0,60})\s*[:=]\s*(?P<value>.+?)\s*$"
)
SENTENCE_PATTERNS = [
    re.compile(
        r"(?i)\bthe\s+(?P<key>[a-z][a-z\s_-]{1,40}?)\s+"
        r"(?:is|are|defaults to|default to|set to|should be|uses?)\s+"
        r"(?P<value>true|false|-?\d+(?:\.\d+)?|\"[^\"]+\"|'[^']+')"
    ),
    re.compile(
        r"(?i)\b(?P<key>retry count|retry attempts|retries|timeout|threshold|limit)\b"
        r".*?\b(?P<value>-?\d+(?:\.\d+)?)\b(?:\s+(?:times|seconds?|minutes?|ms))?"
    ),
]


def _normalize_key(raw_key: str) -> str:
    """Normalize keys into a stable lowercase form."""
    key = raw_key.strip().lower()
    replacements = {
        "retry count": "retries",
        "retry attempts": "retries",
        "retry": "retries",
    }
    key = replacements.get(key, key)
    return re.sub(r"[\s-]+", "_", key)


def _coerce_value(raw_value: str) -> Any | None:
    """Convert extracted text into a comparable Python value."""
    cleaned = raw_value.strip().strip("|").strip()
    lowered = cleaned.lower()
    if re.fullmatch(r"-?\d+", cleaned):
        return int(cleaned)
    if re.fullmatch(r"-?\d+\.\d+", cleaned):
        return float(cleaned)
    if lowered in {"true", "false"}:
        return lowered == "true"
    if (cleaned.startswith('"') and cleaned.endswith('"')) or (
        cleaned.startswith("'") and cleaned.endswith("'")
    ):
        return cleaned[1:-1]
    if re.fullmatch(r"[A-Za-z][\w\s-]{0,60}", cleaned):
        return cleaned
    return None


def _build_claim(key: str, value: Any, text: str, line_number: int) -> dict[str, Any]:
    return {
        "key": _normalize_key(key),
        "value": value,
        "text": text.strip(),
        "line": line_number,
    }


def _dedupe_claims(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, Any, int]] = set()
    unique: list[dict[str, Any]] = []
    for claim in claims:
        marker = (claim["key"], claim["value"], claim["line"])
        if marker in seen:
            continue
        seen.add(marker)
        unique.append(claim)
    return unique


def extract_claims_regex(markdown_text: str) -> list[dict[str, Any]]:
    """Extract claims from key-value lines, tables, and simple sentences."""
    claims: list[dict[str, Any]] = []
    lines = markdown_text.splitlines()

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue

        line_match = LINE_CLAIM_PATTERN.match(line)
        if line_match:
            value = _coerce_value(line_match.group("value"))
            if value is not None:
                claims.append(
                    _build_claim(
                        line_match.group("key"),
                        value,
                        line_match.group(0),
                        index,
                    )
                )
                continue

        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if len(cells) == 2 and not all(set(cell) <= {"-", ":"} for cell in cells):
                value = _coerce_value(cells[1])
                if value is not None and cells[0].lower() not in {"setting", "key", "name", "value"}:
                    claims.append(_build_claim(cells[0], value, line, index))
                    continue

        for pattern in SENTENCE_PATTERNS:
            sentence_match = pattern.search(line)
            if not sentence_match:
                continue
            value = _coerce_value(sentence_match.group("value"))
            if value is None:
                continue
            claims.append(
                _build_claim(
                    sentence_match.group("key"),
                    value,
                    sentence_match.group(0),
                    index,
                )
            )
            break

    return _dedupe_claims(claims)


def extract_claims_llm(markdown_text: str, model: str = "gpt-4.1-mini") -> list[dict[str, Any]]:
    """Use an LLM to extract claims when regex misses richer phrasing."""
    if OpenAI is None:
        return []

    client = OpenAI()
    prompt = (
        "Extract documentation claims that assert configuration values or behavior.\n"
        "Return strict JSON as a list of objects with keys: key, value, text, line.\n"
        "Only include claims with a concrete value. Normalize keys to lowercase snake_case.\n"
        "Documentation:\n"
        f"{markdown_text}"
    )

    response = client.responses.create(
        model=model,
        input=prompt,
    )
    content = response.output_text.strip()
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return []

    claims: list[dict[str, Any]] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        if {"key", "value", "text"} <= set(item):
            claims.append(
                {
                    "key": _normalize_key(str(item["key"])),
                    "value": item["value"],
                    "text": str(item["text"]),
                    "line": int(item.get("line", 0) or 0),
                }
            )
    return _dedupe_claims(claims)


def extract_claims(markdown_text: str, use_llm_fallback: bool = False) -> list[dict[str, Any]]:
    """Extract claims from markdown using regex and optional LLM fallback."""
    regex_claims = extract_claims_regex(markdown_text)
    if regex_claims or not use_llm_fallback:
        return regex_claims
    return extract_claims_llm(markdown_text)

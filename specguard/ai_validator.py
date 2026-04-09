"""AI-assisted validation for documentation drift findings."""

from __future__ import annotations

import os
from typing import Any

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - dependency may be absent in some environments
    OpenAI = None


DEFAULT_RESULT = {
    "status": "uncertain",
    "confidence": 0,
    "reason": "AI validation unavailable.",
}


def validate_claim(
    claim: dict[str, Any],
    code_value: Any,
    context: str,
    model: str = "gpt-4.1-mini",
) -> dict[str, Any]:
    """
    Ask an LLM whether a documentation claim matches the code behavior.

    Falls back gracefully when the API key or client library is missing.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "status": "uncertain",
            "confidence": 0,
            "reason": "OPENAI_API_KEY is not set; skipping AI validation.",
        }

    if OpenAI is None:
        return {
            "status": "uncertain",
            "confidence": 0,
            "reason": "OpenAI package is not installed; skipping AI validation.",
        }

    client = OpenAI(api_key=api_key)
    prompt = (
        "You are validating whether documentation matches code behavior.\n"
        "Respond with exactly three lines:\n"
        "status: correct|incorrect|uncertain\n"
        "confidence: 0-100\n"
        "reason: <brief explanation>\n\n"
        f"Claim: {claim['text']}\n"
        f"Claim key: {claim['key']}\n"
        f"Documented value: {claim['value']}\n"
        f"Code value: {code_value}\n"
        f"Context:\n{context}\n"
    )

    try:
        response = client.responses.create(model=model, input=prompt)
    except Exception as exc:  # pragma: no cover - network/API failures
        return {
            "status": "uncertain",
            "confidence": 0,
            "reason": f"AI validation failed: {exc}",
        }

    status = "uncertain"
    confidence = 0
    reason = "AI response could not be parsed."
    for line in response.output_text.splitlines():
        lowered = line.lower().strip()
        if lowered.startswith("status:"):
            candidate = lowered.split(":", 1)[1].strip()
            if candidate in {"correct", "incorrect", "uncertain"}:
                status = candidate
        elif lowered.startswith("confidence:"):
            raw_confidence = lowered.split(":", 1)[1].strip()
            try:
                confidence = max(0, min(100, int(raw_confidence)))
            except ValueError:
                confidence = 0
        elif lowered.startswith("reason:"):
            reason = line.split(":", 1)[1].strip()

    return {
        "status": status,
        "confidence": confidence,
        "reason": reason,
    }

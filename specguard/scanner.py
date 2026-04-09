"""Orchestrate documentation scanning and AI-assisted validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from specguard.ai_validator import validate_claim
from specguard.code_parser import parse_python_path
from specguard.comparator import compare_claims_to_code
from specguard.extractor import extract_claims


def _claim_with_source(claim: dict[str, Any], doc_path: str) -> dict[str, Any]:
    return {**claim, "source_file": doc_path}


def _validation_context(documentation: str, mismatch: dict[str, Any]) -> str:
    code_location = mismatch.get("code_file")
    code_line = mismatch.get("code_line")
    code_context = mismatch.get("code_context") or "Unavailable"
    doc_location = mismatch.get("doc_file")
    doc_line = mismatch.get("doc_line")
    return (
        f"Documentation file: {doc_location}:{doc_line}\n"
        f"Code file: {code_location}:{code_line}\n"
        f"Code snippet: {code_context}\n"
        "Documentation excerpt:\n"
        f"{documentation}"
    )


def scan(doc_path: str, code_path: str, use_llm_extraction: bool = False) -> dict[str, Any]:
    """Run the full SpecGuard pipeline."""
    documentation = Path(doc_path).read_text(encoding="utf-8")
    claims = [
        _claim_with_source(claim, doc_path)
        for claim in extract_claims(documentation, use_llm_fallback=use_llm_extraction)
    ]
    code_constants = parse_python_path(code_path)
    comparison = compare_claims_to_code(claims, code_constants)

    validations: list[dict[str, Any]] = []
    for mismatch in comparison["mismatches"]:
        claim = {
            "key": mismatch["key"],
            "value": mismatch["doc_value"],
            "text": mismatch["text"],
        }
        validations.append(
            {
                **mismatch,
                "ai_verdict": validate_claim(
                    claim,
                    mismatch["code_value"],
                    _validation_context(documentation, mismatch),
                ),
            }
        )

    return {
        "claims": claims,
        "code_constants": code_constants,
        "matches": comparison["matches"],
        "mismatches": validations,
        "has_drift": bool(validations),
    }

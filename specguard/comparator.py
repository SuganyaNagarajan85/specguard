"""Compare documentation claims against code constants."""

from __future__ import annotations

from typing import Any


STOP_WORDS = {"default", "defaults", "value", "count", "setting", "config"}


def _stem_token(token: str) -> str:
    if token.endswith("ies"):
        return token[:-3] + "y"
    if token.endswith("s") and len(token) > 3:
        return token[:-1]
    return token


def _key_variants(key: str) -> set[str]:
    tokens = [token for token in key.split("_") if token and token not in STOP_WORDS]
    stemmed = [_stem_token(token) for token in tokens]
    variants = {key, "_".join(tokens), "_".join(stemmed), "".join(tokens), "".join(stemmed)}
    return {variant for variant in variants if variant}


def _resolve_code_match(
    claim_key: str, code_constants: dict[str, dict[str, Any]]
) -> tuple[str | None, dict[str, Any] | None]:
    if claim_key in code_constants:
        return claim_key, code_constants[claim_key]

    claim_variants = _key_variants(claim_key)
    for code_key, record in code_constants.items():
        if claim_variants & _key_variants(code_key):
            return code_key, record
    return None, None


def compare_claims_to_code(
    claims: list[dict[str, Any]], code_constants: dict[str, dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    """Return structured matches and mismatches for downstream reporting."""
    matches: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []

    for claim in claims:
        key = claim["key"]
        doc_value = claim["value"]
        matched_key, code_record = _resolve_code_match(key, code_constants)

        if code_record is None:
            mismatches.append(
                {
                    "key": key,
                    "matched_code_key": None,
                    "doc_value": doc_value,
                    "code_value": None,
                    "text": claim["text"],
                    "doc_line": claim.get("line"),
                    "doc_file": claim.get("source_file"),
                    "issue": "missing_in_code",
                }
            )
            continue

        result = {
            "key": key,
            "matched_code_key": matched_key,
            "doc_value": doc_value,
            "code_value": code_record["value"],
            "text": claim["text"],
            "doc_line": claim.get("line"),
            "doc_file": claim.get("source_file"),
            "code_line": code_record.get("line"),
            "code_file": code_record.get("source_file"),
            "code_context": code_record.get("context"),
        }

        if code_record["value"] == doc_value:
            matches.append(result)
        else:
            mismatches.append({**result, "issue": "value_mismatch"})

    return {"matches": matches, "mismatches": mismatches}

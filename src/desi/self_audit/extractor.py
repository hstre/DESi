"""ExplicitClaim extractor — Aufgabe 2.

Pattern-based scan over markdown text. Only four claim kinds are
emitted (hash, numeric, count, phase). Anything else — semantic
free-text claims, narrative paragraphs, opinions — is intentionally
ignored.
"""
from __future__ import annotations

import re
from typing import Iterable

from .claim import ClaimKind, ExplicitClaim, make_claim_id


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------


# 16-hex token. We restrict to LOWERCASE hex to avoid matching all-caps
# words like "TODO" or "AUTHORITY".
_HEX16 = re.compile(r"\b([0-9a-f]{16})\b")

# Known PatchPhase / ResolutionState / ClaimVerdict tokens.
_PHASE_TOKENS: frozenset[str] = frozenset({
    "discovery", "risk_probe", "guard_synthesis",
    "implementation", "regression", "replay_verification",
    "complete",
    "resolution_complete", "resolution_blocked",
    "resolution_cycle_detected", "resolution_depth_exceeded",
    "resolution_incomplete",
    "verified", "missing_artifact", "hash_mismatch",
    "value_mismatch", "ambiguous_reference",
    "parser_loss", "audit_reject_loss", "bridge_missing_loss",
    "consilium_veto_loss", "resolver_not_reached",
    "resolver_zero_depth", "cycle_not_recognized", "no_loss",
    "unknown_loss",
    "causal_chain", "syllogism", "implication", "transitivity",
    "contradiction", "equivalence",
})

# Known numeric keys we promote into NUMERIC claims when paired
# with a decimal on the same line.
_NUMERIC_KEYS: frozenset[str] = frozenset({
    "precision", "recall", "rule_hit_rate", "no_rule_match_rate",
    "false_positives", "multistep_trigger_rate",
    "main_trigger_rate", "known_false_positive_reopen_rate",
    "authority_touch_rate", "philosophy_touch_rate",
    "metaphor_touch_rate", "recursion_reach_rate",
    "bridge_creation_rate", "consilium_call_rate",
    "resolver_entry_rate", "false_depth_zero_rate",
    "cycle_detection_rate", "blocked_propagation_accuracy",
    "best_fitness", "best_depth", "r2_r3_gain_count",
    "r4_regression_count", "r5_regression_count",
    "actionable_deficits", "non_actionable_deficits",
    "highest_severity", "highest_confidence",
    "accepted_steps", "rejected_steps", "killed_steps",
    "total_cases", "total_steps", "total_deficits",
    "safe_candidate_rate", "multi_hop_case_coverage",
    "parser_vs_rule_misclassification_rate",
    "premise_count", "depth_reached",
})


# Numeric token: an optional sign, a digit run with optional decimal.
_DECIMAL = re.compile(r"-?\d+(?:\.\d+)?")

# Ratio: N/M form, only when both are short integers.
_RATIO = re.compile(r"\b(\d{1,4})\s*/\s*(\d{1,4})\b")

# Artifact-path hint on the line: anything starting with "artifacts/"
# or referencing a known doc file.
_ARTIFACT_HINT = re.compile(r"artifacts/[A-Za-z0-9_/.\-]+\.json")


# ---------------------------------------------------------------------------
# Per-line extraction
# ---------------------------------------------------------------------------


def _line_artifact_hint(line: str) -> str:
    m = _ARTIFACT_HINT.search(line)
    return m.group(0) if m else ""


def _emit_hash_claims(
    *, doc_id: str, doc_path: str,
    line_number: int, line_text: str,
) -> Iterable[ExplicitClaim]:
    artifact = _line_artifact_hint(line_text)
    seen: set[str] = set()
    for m in _HEX16.finditer(line_text):
        hexv = m.group(1)
        # Skip all-digit tokens — those are usually unrelated numbers.
        if hexv.isdigit():
            continue
        if hexv in seen:
            continue
        seen.add(hexv)
        # Try to detect the field on the line (replay_hash, sha256...).
        key = ""
        low = line_text.lower()
        for cand in (
            "replay_hash", "benchmark_hash_before",
            "benchmark_hash_after", "stable_hash_before",
            "stable_hash_after", "patch_id", "sha256",
            "fingerprint", "clone_hash", "input_hash",
            "output_hash",
        ):
            if cand in low:
                key = cand
                break
        yield ExplicitClaim(
            claim_id=make_claim_id(
                doc_path, line_number, ClaimKind.HASH, key, hexv,
            ),
            doc_id=doc_id, doc_path=doc_path,
            line_number=line_number, line_text=line_text.strip(),
            kind=ClaimKind.HASH, key=key, value=hexv,
            referenced_artifact=artifact,
        )


def _emit_numeric_claims(
    *, doc_id: str, doc_path: str,
    line_number: int, line_text: str,
) -> Iterable[ExplicitClaim]:
    """Look for known-key + decimal on the same line."""
    artifact = _line_artifact_hint(line_text)
    low = line_text.lower()
    for key in _NUMERIC_KEYS:
        if key not in low:
            continue
        # Find the first decimal after the key occurrence.
        idx = low.find(key)
        tail = line_text[idx:]
        m = _DECIMAL.search(tail[len(key):])
        if not m:
            continue
        value = m.group(0)
        yield ExplicitClaim(
            claim_id=make_claim_id(
                doc_path, line_number, ClaimKind.NUMERIC, key, value,
            ),
            doc_id=doc_id, doc_path=doc_path,
            line_number=line_number, line_text=line_text.strip(),
            kind=ClaimKind.NUMERIC, key=key, value=value,
            referenced_artifact=artifact,
        )


def _emit_count_claims(
    *, doc_id: str, doc_path: str,
    line_number: int, line_text: str,
) -> Iterable[ExplicitClaim]:
    """N/M ratios where M is small enough to be a real count."""
    artifact = _line_artifact_hint(line_text)
    seen: set[tuple[str, str]] = set()
    for m in _RATIO.finditer(line_text):
        n, k = m.group(1), m.group(2)
        try:
            ki = int(k)
        except ValueError:
            continue
        # Skip dates (e.g. 2026/05/15) — both parts too small to be
        # benchmark sizes? 30 and 50 fit; days don't. Use bounds.
        if ki > 2000:
            continue
        if ki == 0:
            continue
        if (n, k) in seen:
            continue
        seen.add((n, k))
        yield ExplicitClaim(
            claim_id=make_claim_id(
                doc_path, line_number, ClaimKind.COUNT,
                "ratio", f"{n}/{k}",
            ),
            doc_id=doc_id, doc_path=doc_path,
            line_number=line_number, line_text=line_text.strip(),
            kind=ClaimKind.COUNT, key="ratio", value=f"{n}/{k}",
            referenced_artifact=artifact,
        )


def _emit_phase_claims(
    *, doc_id: str, doc_path: str,
    line_number: int, line_text: str,
) -> Iterable[ExplicitClaim]:
    artifact = _line_artifact_hint(line_text)
    low = line_text.lower()
    for token in _PHASE_TOKENS:
        if token not in low:
            continue
        # The token must appear as a whole-word match.
        if not re.search(rf"\b{re.escape(token)}\b", low):
            continue
        # Heuristic: avoid emitting on enum-definition lines like
        # "* RESOLUTION_COMPLETE — ...". The line must look like a
        # claim (contain ':', '=', '|', or "phase").
        if not any(ch in line_text for ch in (":", "=", "|")):
            continue
        yield ExplicitClaim(
            claim_id=make_claim_id(
                doc_path, line_number, ClaimKind.PHASE, "phase", token,
            ),
            doc_id=doc_id, doc_path=doc_path,
            line_number=line_number, line_text=line_text.strip(),
            kind=ClaimKind.PHASE, key="phase", value=token,
            referenced_artifact=artifact,
        )


# ---------------------------------------------------------------------------
# Top-level extractor
# ---------------------------------------------------------------------------


def extract_claims_from_text(
    *, doc_id: str, doc_path: str, text: str,
) -> tuple[ExplicitClaim, ...]:
    """Run all four extractors over each line."""
    claims: list[ExplicitClaim] = []
    for n, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        for fn in (
            _emit_hash_claims, _emit_phase_claims,
            _emit_numeric_claims, _emit_count_claims,
        ):
            claims.extend(fn(
                doc_id=doc_id, doc_path=doc_path,
                line_number=n, line_text=line,
            ))
    return tuple(claims)


__all__ = ["extract_claims_from_text"]

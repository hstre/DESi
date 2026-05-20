"""Aufgabe 10 — reproducibility checks.

Two independent loads of the paper and claims must produce
identical content hashes.
"""
from __future__ import annotations

import hashlib
import json
import pathlib

from ._helpers import load_claims


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_PAPER_PATH = (
    _REPO_ROOT / "docs" / "papers"
    / "v3_gate_governed_architecture.md"
)
_CLAIMS_PATH = (
    _REPO_ROOT / "docs" / "papers" / "v3_claims.json"
)


def _paper_hash() -> str:
    return hashlib.sha256(
        _PAPER_PATH.read_bytes(),
    ).hexdigest()[:16]


def _claims_hash() -> str:
    # Canonical-JSON hash of the parsed claims object so
    # whitespace / ordering does not change the hash.
    data = json.loads(_CLAIMS_PATH.read_text(encoding="utf-8"))
    raw = json.dumps(
        data, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def test_paper_hash_deterministic() -> None:
    a = _paper_hash()
    b = _paper_hash()
    assert a == b


def test_claims_hash_deterministic() -> None:
    a = _claims_hash()
    b = _claims_hash()
    assert a == b


def test_load_claims_idempotent() -> None:
    a = load_claims()
    b = load_claims()
    assert a == b


def test_paper_contains_all_required_sections() -> None:
    """Aufgabe 4 — 15 exact section headings."""
    text = _PAPER_PATH.read_text(encoding="utf-8")
    required = (
        "## 1. Problem",
        "## 2. Prior Failure Modes",
        "## 3. Frame Declaration",
        "## 4. Frame Tension",
        "## 5. Routing Authority",
        "## 6. CAUSAL_CHAIN",
        "## 7. Suspension Gates",
        "## 8. Adversarial Findings",
        "## 9. Gate Ablation",
        "## 10. Gate Ordering",
        "## 11. Latency Orthogonality",
        "## 12. Limitations",
        "## 13. Falsified Hypotheses",
        "## 14. Deployment Criteria",
        "## 15. Conclusion",
    )
    missing = [s for s in required if s not in text]
    assert missing == [], f"missing sections: {missing}"


def test_paper_lists_at_least_ten_failed_hypotheses() -> None:
    text = _PAPER_PATH.read_text(encoding="utf-8")
    # Falsified Hypotheses section uses 1./ 2./ ... numbered list.
    section_start = text.index("## 13. Falsified Hypotheses")
    section_end = text.index("## 14. Deployment Criteria")
    section = text[section_start:section_end]
    # Count numbered items "1." through "10."
    count = sum(
        1 for n in range(1, 30) if f"\n{n}. " in section
    )
    assert count >= 10, (
        f"only {count} failed hypotheses listed; ≥ 10 required"
    )

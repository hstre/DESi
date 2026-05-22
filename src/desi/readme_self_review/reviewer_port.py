"""README/System-Paper self-review - Reviewer Port input layer.

Loads the exact reviewed README snapshot (System Paper v1.1) and runs
the deterministic scanners the audit needs: the forbidden-term scan,
the built-in-hash high-risk pattern, the internal compression-range
consistency check, the regression-table freshness check (against the
committed regression-status artifacts), and the three structural
checks (synthetic/real separation, external-generalization guard,
replay explanation).

IMPORTANT framing: this is an INTERNAL CONSISTENCY AND OVERREACH AUDIT
of DESi's own documentation. It is NOT self-validation. DESi treats
the README as an external claim artifact and does not confer
authority on it.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re

from desi.scientific_rendering import FORBIDDEN_TERMS, forbidden_hits

AUDIT_FRAMING = (
    "DESi performs an internal consistency and overreach audit of "
    "its own documentation. DESi does not validate itself."
)

_ROOT = pathlib.Path(__file__).resolve().parents[3]
_SNAPSHOT = (
    pathlib.Path(__file__).resolve().parent
    / "reviewed_readme_v1_1.md"
)


def reviewed_text() -> str:
    return _SNAPSHOT.read_text(encoding="utf-8")


def reviewed_hash() -> str:
    return hashlib.sha256(
        _SNAPSHOT.read_bytes(),
    ).hexdigest()


# --- forbidden-term / scanner risk --------------
def forbidden_term_hits() -> tuple[str, ...]:
    return forbidden_hits(reviewed_text())


def builtin_hash_pattern_hits() -> int:
    return len(re.findall(r"\bhash\(", reviewed_text()))


# --- internal numeric consistency ---------------
def compression_range_phrasings() -> dict[str, int]:
    t = reviewed_text()
    return {
        p: t.count(p)
        for p in ("41–60%", "42–50%", "~42%", "42–60%")
        if t.count(p) > 0
    }


def compression_range_consistent() -> bool:
    return len(compression_range_phrasings()) <= 1


# --- regression-table freshness -----------------
def _committed_regression_counts() -> dict[str, int]:
    out: dict[str, int] = {}
    for name, path in (
        ("v31", "artifacts/peripheral_mutation/_regression_status.json"),
        ("v32", "artifacts/frozen_benchmark/_regression_status.json"),
    ):
        p = _ROOT / path
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            out[name] = int(data.get("passed_count", 0))
    return out


def stale_regression_runs() -> tuple[str, ...]:
    """Committed full-regression runs that the README's milestone
    table omits."""
    t = reviewed_text()
    missing = []
    for name, count in _committed_regression_counts().items():
        if str(count) not in t and f"{count:,}" not in t:
            missing.append(f"{name}={count}")
    return tuple(missing)


# --- structural checks --------------------------
def synthetic_real_separation_present() -> bool:
    t = reviewed_text().lower()
    return (
        "synthetic or locally vendored" in t
        and "not live benchmark leaderboards" in t
        and "only phase involving real external api" in t
    )


def external_generalization_guard_present() -> bool:
    t = reviewed_text().lower()
    return (
        "what the results do not support" in t
        and "not a measured result" in t
        and "generalization to production workloads" in t
    )


def replay_explanation_present() -> bool:
    t = reviewed_text().lower()
    return (
        "bit-exact reproducible" in t
        and "hashlib.sha256" in t
        and "no prng" in t
    )


def reviewer_port_module_present() -> bool:
    """The paper calls the Reviewer Port central; is there a module
    literally named that?"""
    return (_ROOT / "src" / "desi" / "reviewer_port.py").exists()


__all__ = [
    "AUDIT_FRAMING",
    "FORBIDDEN_TERMS",
    "builtin_hash_pattern_hits",
    "compression_range_consistent",
    "compression_range_phrasings",
    "external_generalization_guard_present",
    "forbidden_term_hits",
    "replay_explanation_present",
    "reviewed_hash",
    "reviewed_text",
    "reviewer_port_module_present",
    "stale_regression_runs",
    "synthetic_real_separation_present",
]

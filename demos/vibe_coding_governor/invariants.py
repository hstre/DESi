"""Explicit, machine-checkable governance invariants over the structural state.

Each invariant is a closed predicate that returns a list of human-readable violation
strings (empty == satisfied). They are evaluated through the REAL DESi Concept Gate
(`desi.gates.concept_gate`): each invariant becomes a GateCondition whose `passed` is
`violations == 0`, and the candidate is gate-accepted only if `passes_all` holds
(closed-gate semantics). Invariants are replayable (pure functions of the state) and
explicit (listed here, not hidden in a model).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from desi.gates.concept_gate import GateCondition, evaluate, failing, passes_all  # noqa: E402

from analysis import PUBLIC_ROUTES  # noqa: E402


def _inv_auth_all_routes(state) -> list:
    return [f"route {r['path']} ({'/'.join(r['methods'])}) has no auth"
            for r in state["routes"] if r["path"] not in PUBLIC_ROUTES and not r["auth"]]


def _inv_no_plaintext_passwords(state) -> list:
    return [f"execute writes a password column without hashing: {e['sql'][:60]!r}"
            for e in state["executes"] if e["writes_password"] and not e["hashed"]]


def _inv_no_raw_sql(state) -> list:
    return [f"string-built SQL (injection risk): {e['sql'][:60]!r}"
            for e in state["executes"] if e["raw"]]


def _inv_no_secret_logging(state) -> list:
    return [f"{s['func']}() logs secret(s) {', '.join(s['names'])}"
            for s in state["secret_logs"]]


def _inv_deterministic_migrations(state) -> list:
    out = [f"migration v{m['version']} is non-deterministic: {m['sql'][:60]!r}"
           for m in state["migrations"] if m["nondeterministic"]]
    versions = [m["version"] for m in state["migrations"]]
    if versions != sorted(set(versions)):
        out.append(f"migration versions not strictly increasing/unique: {versions}")
    return out


def _inv_data_model_consistency(state) -> list:
    return [f"query references undeclared column {c!r}" for c in state["undeclared_referenced"]]


INVARIANTS = (
    ("AUTH_ALL_ROUTES", "every non-public API route requires authentication", _inv_auth_all_routes),
    ("NO_PLAINTEXT_PASSWORDS", "passwords are never stored/compared in plaintext", _inv_no_plaintext_passwords),
    ("NO_RAW_SQL", "no string-built SQL (parameterized queries only)", _inv_no_raw_sql),
    ("NO_SECRET_LOGGING", "secrets/passwords/tokens are never logged", _inv_no_secret_logging),
    ("DETERMINISTIC_MIGRATIONS", "schema migrations are deterministic and monotonically versioned",
     _inv_deterministic_migrations),
    ("DATA_MODEL_CONSISTENCY", "queries only reference declared schema columns", _inv_data_model_consistency),
)


def evaluate_invariants(state):
    """Return (gate_conditions, violations_by_invariant). A condition passes iff its
    invariant produced zero violations."""
    conditions, violations = [], {}
    for inv_id, _desc, fn in INVARIANTS:
        vs = fn(state)
        if vs:
            violations[inv_id] = vs
        conditions.append(GateCondition(name=inv_id, value=float(len(vs)), threshold=0.0,
                                        comparator="==", passed=(len(vs) == 0)))
    return conditions, violations


def gate_accepts(state) -> bool:
    conditions, _ = evaluate_invariants(state)
    return passes_all(conditions)


def failing_invariants(state):
    conditions, _ = evaluate_invariants(state)
    return failing(conditions)

"""Mutation probe for the router governance core — are the tests enough to PIN the logic?

A manual dev tool (like the live-loop benchmarks): for each module it applies a fixed set of
decision-critical source mutations one at a time, runs the ``tests/router_governance`` suite, and
reports each as *killed* (suite fails → the logic is pinned) or *SURVIVED* (suite passes → a coverage
gap or a provably-equivalent mutant). Serial, guarded by ``try/finally`` so every file is restored.

    python -m desi_router.governance.benchmark.mutation_probe            # all modules
    python -m desi_router.governance.benchmark.mutation_probe modes      # one module

Covers the decision core (``modes.py``), the cross-lingual classifier (``clsp.py``) and the five
plausible-wrong-slice checks. Known equivalent survivors in ``modes.py``: the discrete risk lattice
never yields ``wrong_state_poisoning == 0.7`` nor a ``max(risk) == 0.4``, so the ``>=`` boundaries at
``_HIGH``/``_MOD`` have slack — there is no off-by-one to catch.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_GOV = Path(__file__).resolve().parents[1]
_SUITE = Path(__file__).resolve().parents[3] / "tests" / "router_governance"

# module -> list of (label, old, new); each `old` must occur exactly once in that module.
_MUTATIONS: dict[str, list[tuple[str, str, str]]] = {
    "modes.py": [
        ("poison>=_HIGH -> >_HIGH [equiv: 0.7 unreachable]",
         'r["wrong_state_poisoning"] >= _HIGH and report.wrong_frame_present',
         'r["wrong_state_poisoning"] > _HIGH and report.wrong_frame_present'),
        ("poison>=_HIGH -> >=_MOD [equiv: (0.1,0.8) gap]",
         'if r["wrong_state_poisoning"] >= _HIGH:\n        return decision(GUARDED',
         'if r["wrong_state_poisoning"] >= _MOD:\n        return decision(GUARDED'),
        ("max>=_MOD -> >_MOD [equiv: max==0.4 unreachable]",
         'if max(r.values()) >= _MOD:', 'if max(r.values()) > _MOD:'),
        ("max>=_MOD -> >=_HIGH (weaken caution)",
         'if max(r.values()) >= _MOD:', 'if max(r.values()) >= _HIGH:'),
        ("clean state_slice may_update True->False",
         'return decision(STATE_SLICE, "clean usable state, low risk", may_update=True)',
         'return decision(STATE_SLICE, "clean usable state, low risk", may_update=False)'),
        ("NORMAL may_update True->False",
         'return decision(NORMAL, "no state needed, low risk", may_update=True, sources=())',
         'return decision(NORMAL, "no state needed, low risk", may_update=False, sources=())'),
        ("user_specific_missing flip", 'if report.user_specific_missing:',
         'if not report.user_specific_missing:'),
        ("not has_usable_state flip", 'if not report.has_usable_state and retrieval_available:',
         'if report.has_usable_state and retrieval_available:'),
        ("omitted_opposition flip", 'if report.omitted_opposition_ids:',
         'if not report.omitted_opposition_ids:'),
        ("invalidated and->or (over-block)",
         'if (report.invalidated_claim_ids or report.superseded_claim_ids) '
         'and report.task_touches_invalidated:',
         'if (report.invalidated_claim_ids or report.superseded_claim_ids) '
         'or report.task_touches_invalidated:'),
        ("conflict and->or",
         'if report.open_conflict_ids and report.answer_requires_conflict_resolution:',
         'if report.open_conflict_ids or report.answer_requires_conflict_resolution:'),
        ("verifier gate flip", 'if decision.validator_required and not verifier_ok:',
         'if decision.validator_required and verifier_ok:'),
    ],
    "clsp.py": [
        ("overamp and->or", 'return orig_hedged and proj_strong',
         'return orig_hedged or proj_strong'),
        ("overamp drop 'not' (hedged-AND-strong)",
         'orig_hedged = _hedged(original_span or "") and not _has_strength(original_span or "")',
         'orig_hedged = _hedged(original_span or "") and _has_strength(original_span or "")'),
        ("invariant_core promotable True->False", 'return CLSPResult(INVARIANT_CORE, True,',
         'return CLSPResult(INVARIANT_CORE, False,'),
        ("probe_only False->True (lead-language breach)",
         'return CLSPResult(PROBE_ONLY_CANDIDATE, False,',
         'return CLSPResult(PROBE_ONLY_CANDIDATE, True,'),
        ("emergent anchor in->not in", 'if c.lead_anchor in (STRONG, WEAK):',
         'if c.lead_anchor not in (STRONG, WEAK):'),
        ("invariant >=2 -> >=1 langs", 'if c.lead_anchor == STRONG and len(c.languages) >= 2:',
         'if c.lead_anchor == STRONG and len(c.languages) >= 1:'),
        ("semantic_loss and->or", 'if c.lost_in_projection and c.lead_anchor != NONE:',
         'if c.lost_in_projection or c.lead_anchor != NONE:'),
    ],
    "provenance.py": [
        ("thin >=2 -> >2 claims", 'bool(n_claims >= 2 and 0 < independent <= 1)',
         'bool(n_claims > 2 and 0 < independent <= 1)'),
        ("thin <=1 -> <=2 roots", 'bool(n_claims >= 2 and 0 < independent <= 1)',
         'bool(n_claims >= 2 and 0 < independent <= 2)'),
        ("thin and->or", 'bool(n_claims >= 2 and 0 < independent <= 1)',
         'bool(n_claims >= 2 or 0 < independent <= 1)'),
        ("all_derived all->any", 'len(derived) == n_claims and all(derived)',
         'len(derived) == n_claims and any(derived)'),
    ],
    "scope.py": [
        ("empty-scope guard flip", 'if not task_scope:', 'if task_scope:'),
        ("mismatch !=->==", 'if s and s != task_scope:', 'if s and s == task_scope:'),
    ],
    "supersession.py": [
        ("omitted not in->in", 'if sib and sib not in surfaced:', 'if sib and sib in surfaced:'),
    ],
    "missing_opposition.py": [
        ("omitted not in->in", 'if o and o not in surfaced:', 'if o and o in surfaced:'),
    ],
    "k_stability.py": [
        ("escalated >-> >=", 'escalated = _RANK.get(wm, 0) > _RANK.get(nm, 0)',
         'escalated = _RANK.get(wm, 0) >= _RANK.get(nm, 0)'),
        ("unstable or->and", 'bool(escalated or update_withdrawn)',
         'bool(escalated and update_withdrawn)'),
    ],
}


def _suite_passes() -> bool:
    # PYTHONDONTWRITEBYTECODE: never cache the MUTATED source as a .pyc. Without it, a mutant compiled
    # in the same wall-clock second as the restore leaves a stale .pyc that shadows the restored source
    # (pyc invalidation is 1-second granular) — poisoning every later run. Belt-and-suspenders below.
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    r = subprocess.run([sys.executable, "-m", "pytest", str(_SUITE), "-q", "-x",
                        "-p", "no:cacheprovider"], capture_output=True, text=True, env=env)
    return r.returncode == 0


def _run_module(name: str, muts: list[tuple[str, str, str]]) -> tuple[list[str], list[tuple[str, str]]]:
    target = _GOV / name
    src = target.read_text()
    killed: list[str] = []
    survived: list[tuple[str, str]] = []
    try:
        for label, old, new in muts:
            if src.count(old) != 1:
                survived.append((label, "PATTERN-NOT-UNIQUE"))
                continue
            target.write_text(src.replace(old, new, 1))
            (survived.append((label, "SURVIVED")) if _suite_passes() else killed.append(label))
    finally:
        target.write_text(src)
        # drop any cached bytecode for this module so the restored source is always re-read fresh
        for pyc in (_GOV / "__pycache__").glob(f"{target.stem}.*.pyc"):
            pyc.unlink(missing_ok=True)
    return killed, survived


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    only = argv[0] if argv else None
    total_k = total_s = 0
    for name, muts in _MUTATIONS.items():
        if only and only not in name:
            continue
        killed, survived = _run_module(name, muts)
        total_k += len(killed)
        total_s += len(survived)
        print(f"\n{name}: {len(muts)} mutants | killed {len(killed)} | survived {len(survived)}")
        for label in killed:
            print(f"  killed   · {label}")
        for label, why in survived:
            print(f"  SURVIVED · {label} ({why})")
    print(f"\nTOTAL killed {total_k} | survived {total_s}")
    print("restore-sanity suite green:", _suite_passes())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

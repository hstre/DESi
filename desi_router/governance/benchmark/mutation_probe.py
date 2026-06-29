"""Mutation probe for the router decision core — are the tests enough to PIN the logic?

A manual dev tool (like the live-loop benchmarks): it applies a fixed set of decision-critical source
mutations to ``modes.py`` one at a time, runs the ``tests/router_governance`` suite, and reports each
as *killed* (suite fails → the logic is pinned) or *SURVIVED* (suite passes → a coverage gap or an
equivalent mutant). Serial and guarded by ``try/finally`` so the file is always restored.

    python -m desi_router.governance.benchmark.mutation_probe

Last run: 12 mutants, **9 killed**. The 3 survivors are **provably equivalent**, not gaps: the
discrete risk lattice never produces ``wrong_state_poisoning == 0.7`` nor a ``max(risk) == 0.4``, so
the ``>=`` vs ``>`` boundary at ``_HIGH``/``_MOD`` has slack — there is no off-by-one to catch (the
constants could be anywhere in their slack interval with identical behaviour). The one real gap this
found — an ``and`` → ``or`` on the invalidated-claim rule that over-blocks a present-but-untouched
invalid claim — is now pinned by ``test_invalidated_present_but_not_touched_is_state_slice_not_guarded``.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_TARGET = Path(__file__).resolve().parents[1] / "modes.py"
_SUITE = Path(__file__).resolve().parents[3] / "tests" / "router_governance"

# (label, old, new) — each `old` must occur exactly once in modes.py
_MUTATIONS = [
    ("poison>=_HIGH -> >_HIGH [equivalent: 0.7 unreachable]",
     'r["wrong_state_poisoning"] >= _HIGH and report.wrong_frame_present',
     'r["wrong_state_poisoning"] > _HIGH and report.wrong_frame_present'),
    ("poison>=_HIGH -> >=_MOD [equivalent: (0.1,0.8) gap]",
     'if r["wrong_state_poisoning"] >= _HIGH:\n        return decision(GUARDED',
     'if r["wrong_state_poisoning"] >= _MOD:\n        return decision(GUARDED'),
    ("max>=_MOD -> >_MOD [equivalent: max==0.4 unreachable]",
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
]


def _suite_passes() -> bool:
    r = subprocess.run([sys.executable, "-m", "pytest", str(_SUITE), "-q", "-x",
                        "-p", "no:cacheprovider"], capture_output=True, text=True)
    return r.returncode == 0


def main() -> int:
    src = _TARGET.read_text()
    killed, survived = [], []
    try:
        for label, old, new in _MUTATIONS:
            if src.count(old) != 1:
                survived.append((label, "PATTERN-NOT-UNIQUE"))
                continue
            _TARGET.write_text(src.replace(old, new, 1))
            (survived.append((label, "SURVIVED")) if _suite_passes() else killed.append(label))
    finally:
        _TARGET.write_text(src)
    print(f"mutants {len(_MUTATIONS)} | killed {len(killed)} | survived {len(survived)}")
    for label in killed:
        print(f"  killed   · {label}")
    for label, why in survived:
        print(f"  SURVIVED · {label} ({why})")
    print("restore-sanity suite green:", _suite_passes())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

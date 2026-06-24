"""Run the deterministic router-governance benchmark and print the baseline comparison.

    python -m desi_router.governance.benchmark.run

No model calls, no cost. Prints one row per baseline across the metric groups, the per-class mode
accuracy for the DESi router, and a short verdict that reads the trade-off honestly.
"""
from __future__ import annotations

from collections import defaultdict

from desi_router.governance.benchmark.baselines import BASELINES
from desi_router.governance.benchmark.cases import CASES
from desi_router.governance.benchmark.metrics import evaluate

_COLS = [("mode_accuracy", "mode_acc"), ("verifier_recall", "verif_rec"),
         ("update_block_recall", "blk_rec"), ("enforcement_recall", "enforce"),
         ("overblocking_rate", "overblock"), ("unnecessary_verifier_rate", "unnec_verif")]


def _fmt(v):
    return "  —  " if v is None else f"{v:>5.2f}"


def _per_class(policy):
    by = defaultdict(lambda: [0, 0])
    for c in CASES:
        d = policy(c.report(), retrieval_available=c.retrieval_available,
                   anti_delphi_available=c.anti_delphi_available)
        by[c.klass][1] += 1
        by[c.klass][0] += d.chosen_mode in c.expected_modes
    return {k: (hit / tot) for k, (hit, tot) in sorted(by.items())}


def main() -> None:
    print(f"Router-governance benchmark · {len(CASES)} fixture cases · deterministic, no LLM\n")
    head = "baseline".ljust(22) + "".join(lbl.rjust(11) for _, lbl in _COLS)
    print(head)
    print("-" * len(head))
    results = {}
    for name, policy in BASELINES.items():
        m = evaluate(policy)
        results[name] = m
        row = name.ljust(22) + "".join(_fmt(m[key]).rjust(11) for key, _ in _COLS)
        print(row)

    print("\nPer-class mode accuracy · B6_desi_router:")
    pc = _per_class(BASELINES["B6_desi_router"])
    print("  " + "  ".join(f"{k}={v:.2f}" for k, v in pc.items()))

    desi = results["B6_desi_router"]
    guard = results["B4_always_guarded"]
    norm = results["B1_always_normal"]
    print("\nVerdict (reads the trade-off, not a victory lap):")
    print(f"  · DESi vs always_guarded: same update-block recall "
          f"({_fmt(desi['update_block_recall']).strip()} vs {_fmt(guard['update_block_recall']).strip()})"
          f", but over-blocking {_fmt(desi['overblocking_rate']).strip()} vs "
          f"{_fmt(guard['overblocking_rate']).strip()} — selective, not paranoid.")
    print(f"  · DESi vs always_normal: verifier-recall {_fmt(desi['verifier_recall']).strip()} vs "
          f"{_fmt(norm['verifier_recall']).strip()} — the unsafe extreme never verifies.")
    low = [k for k, v in pc.items() if v < 1.0]
    if low:
        print(f"  · DESi mode mismatches remain in class(es) {low} — a real finding, not hidden.")
    else:
        print("  · DESi matches the expected mode in every class (expected: labels encode the same "
              "intent it implements — see cases.py caveat).")


if __name__ == "__main__":
    main()

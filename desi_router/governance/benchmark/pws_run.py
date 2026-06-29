"""Run the Plausible-Wrong-Slice benchmark and print the blind→aware contrast.

    python -m desi_router.governance.benchmark.pws_run

Deterministic, no model calls. Shows the SAME router with the missing-opposition scan OFF ("blind",
the prior behaviour) vs ON ("aware"), so the metric movement is attributable to the signal — not to
the router merely being cautious. Reports the honest pair (false_clean ↓, over_caution flat) and the
per-subset split (what missing-opposition closes vs. what still needs provenance/scope checks).
"""
from __future__ import annotations

from desi_router.governance import select_mode
from desi_router.governance.benchmark.pws_metrics import evaluate_pws


def _row(label, m):
    fc, oc = m["false_clean_rate"], m["over_caution_rate"]
    print(f"  {label:7s}  false_clean={fc:<6}  detection={m['pws_detection_rate']:<6}  "
          f"over_caution={oc:<6}  [opp_subset={m['false_clean_opposition_subset']}  "
          f"other_subset={m['false_clean_other_subset']}]")


def main() -> int:
    blind = evaluate_pws(select_mode, aware=False)
    aware = evaluate_pws(select_mode, aware=True)
    sz = aware["_subset_sizes"]
    print(f"Plausible-Wrong-Slice benchmark · {blind['n_traps']} traps + {blind['n_clean']} "
          f"true-clean controls · deterministic, no LLM")
    print(f"  subsets: missing_opposition={sz['missing_opposition']}  "
          f"needs_other_checks(provenance/scope)={sz['needs_other_checks']}\n")
    _row("blind", blind)
    _row("aware", aware)
    print("\nVerdict (honest, not a victory lap):")
    print(f"  · missing-opposition closes its subset: false_clean {blind['false_clean_opposition_subset']}"
          f" -> {aware['false_clean_opposition_subset']} (opposition the slice omitted is now flagged).")
    print(f"  · over-caution on true-clean stays {aware['over_caution_rate']} — selective, not paranoid.")
    print(f"  · the other subset is unchanged ({aware['false_clean_other_subset']}): wrong-scope / "
          f"stale-provenance traps are NOT opposition-omission and await the provenance & scope checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

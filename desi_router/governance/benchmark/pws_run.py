"""Run the Plausible-Wrong-Slice benchmark and print the blind→aware contrast.

    python -m desi_router.governance.benchmark.pws_run

Deterministic, no model calls. Shows the SAME router with the slice-quality scans OFF ("blind", the
prior behaviour) vs ON ("aware"), so metric movement is attributable to the signals — not to the
router merely being cautious. Reports the honest pair (false_clean ↓, over_caution flat) and the
per-check subset split (opposition / provenance / scope), so any remaining gap is named, not hidden.
"""
from __future__ import annotations

from desi_router.governance import select_mode
from desi_router.governance.benchmark.pws_metrics import evaluate_pws


def _fmt(x):
    return "—" if x is None else f"{x:.3f}"


def _row(label, m):
    sub = m["false_clean_by_subset"]
    print(f"  {label:6s} false_clean={_fmt(m['false_clean_rate'])}  detection={_fmt(m['pws_detection_rate'])}"
          f"  over_caution={_fmt(m['over_caution_rate'])}   "
          f"[opp={_fmt(sub['missing_opposition'])} prov={_fmt(sub['provenance_entropy'])} "
          f"scope={_fmt(sub['scope_match'])}]")


def main() -> int:
    blind = evaluate_pws(select_mode, aware=False)
    aware = evaluate_pws(select_mode, aware=True)
    sz = aware["_subset_sizes"]
    print(f"Plausible-Wrong-Slice benchmark · {blind['n_traps']} traps + {blind['n_clean']} "
          f"true-clean controls · deterministic, no LLM")
    print(f"  subsets: opposition={sz['missing_opposition']}  provenance={sz['provenance_entropy']}  "
          f"scope={sz['scope_match']}\n")
    _row("blind", blind)
    _row("aware", aware)
    print("\nVerdict (honest, not a victory lap):")
    print(f"  · overall false_clean {_fmt(blind['false_clean_rate'])} -> {_fmt(aware['false_clean_rate'])} "
          f"with three deterministic checks (no LLM judge).")
    print(f"  · over-caution on true-clean stays {_fmt(aware['over_caution_rate'])} — selective, not paranoid.")
    print("  · each subset is driven by its own signal; any subset still >0 names a check not yet built.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

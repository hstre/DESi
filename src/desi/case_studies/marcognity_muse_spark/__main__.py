"""Reproduction CLI — regenerate the case-study artifacts (Aufgabe 6, reproduction).

    python -m desi.case_studies.marcognity_muse_spark            # regenerate in place
    python -m desi.case_studies.marcognity_muse_spark --out-dir /tmp/cs --ledger led.sqlite

Deterministic and offline: no LLM is called; the analysis is rule-based over the
frozen material fixture. Writes claims.jsonl, evidence.jsonl, contradictions.md,
comparison.md and summary.json. With ``--ledger`` it also appends a hash-chained
audit record via the checkout-only ``desi_router.ledger`` (as
``desi.context_contamination`` does) and verifies the chain.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from . import report


def _load_layer9_ledger():
    """Load the checkout-only Layer-9 ledger by path, or None (see the same
    pattern in ``desi.context_contamination.__main__``). ``desi_router`` is
    deliberately not a dependency of the packaged ``desi`` distribution."""
    import importlib.util

    ledger_py = Path(__file__).resolve().parents[4] / "desi_router" / "ledger.py"
    if not ledger_py.exists():
        return None
    spec = importlib.util.spec_from_file_location("_desi_layer9_ledger", ledger_py)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Ledger


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m desi.case_studies.marcognity_muse_spark",
        description="Regenerate the MarCognity / Muse Spark 1.1 DESi case study.",
    )
    ap.add_argument("--out-dir", default=str(Path(__file__).resolve().parent),
                    help="where to write the artifacts (default: the package dir)")
    ap.add_argument("--ledger", default=None,
                    help="append a hash-chained audit record to this SQLite ledger")
    ap.add_argument("--print-summary", action="store_true",
                    help="print the summary JSON to stdout")
    args = ap.parse_args(argv)

    out_dir = Path(args.out_dir)
    written = report.write_all(out_dir)
    summ = report.summary()

    print(f">> MarCognity / Muse Spark 1.1 case study regenerated in {written['out_dir']}")
    print(f"   claims.jsonl: {written['claims']} claims   evidence.jsonl: "
          f"{written['evidence']} entries")
    print(f"   structural contradictions: {', '.join(summ['structural_contradictions'])}")
    print(f"   source-gate admissible: {summ['source_gate_admissible']}/"
          f"{summ['source_gate_total']}")
    print(f"   self-sealing: {summ['self_sealing']['is_self_sealing']} "
          f"(falsifiers stated: {summ['self_sealing']['falsifiers_stated_in_experiment']})")
    print("   verdicts:", json.dumps(summ["verdict_distribution"], ensure_ascii=False))

    if args.ledger:
        ledger_cls = _load_layer9_ledger()
        if ledger_cls is None:
            print("[--ledger unavailable] desi_router/ledger.py not found — run from "
                  "a repo checkout (the router is not part of the pip distribution).")
            return 2
        led = ledger_cls(args.ledger, instance_id="marcognity_muse_spark")
        rec = led.record("case_study_run", summ)
        ok = led.verify_chain()
        print(f"   ledger: appended seq #{rec['seq']} (chain intact: {ok}) -> {args.ledger}")
        led.close()

    if args.print_summary:
        print(json.dumps(summ, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

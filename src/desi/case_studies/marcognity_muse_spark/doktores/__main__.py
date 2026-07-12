"""Reproduction CLI for the Doktores audit.

    python -m desi.case_studies.marcognity_muse_spark.doktores

Deterministic and offline (no LLM). Writes the audit artifacts into this package
directory. With ``--ledger`` it appends a hash-chained audit record (timestamped)
via the checkout-only ``desi_router.ledger`` and verifies the chain — the only
place a wall-clock timestamp is recorded, so the committed artifacts stay
byte-deterministic. A non-``passed`` overall attestation returns a non-zero exit
code, so a failed audit is never reported as a successful confirmation.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from . import engine
from .models import AttestationRating


def _load_layer9_ledger():
    import importlib.util

    ledger_py = Path(__file__).resolve().parents[5] / "desi_router" / "ledger.py"
    if not ledger_py.exists():
        return None
    spec = importlib.util.spec_from_file_location("_desi_layer9_ledger", ledger_py)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Ledger


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m desi.case_studies.marcognity_muse_spark.doktores",
        description="Adversarial Doktores audit of the DESi case study (deterministic).")
    ap.add_argument("--out-dir", default=str(Path(__file__).resolve().parent),
                    help="where to write the audit artifacts (default: the package dir)")
    ap.add_argument("--ledger", default=None,
                    help="append a hash-chained, timestamped audit record to this SQLite ledger")
    ap.add_argument("--print-summary", action="store_true")
    args = ap.parse_args(argv)

    out_dir = Path(args.out_dir)
    written = engine.write_all(out_dir)
    summ = engine.audit_summary()

    print(">> Doktores rule-guided self-audit (logic/provenance-adversarial, not "
          f"independent; deterministic, offline) written to {written['out_dir']}")
    print(f"   {engine.HEADLINE}")
    print(f"   claims reviewed: {summ['claims_reviewed']} | consensus: "
          f"{json.dumps(summ['consensus_distribution'], ensure_ascii=False)}")
    pr = summ["process_revisions"]
    print(f"   verdicts overturned by THIS audit: "
          f"{summ['verdicts_overturned_by_this_audit']} | with dissent: "
          f"{summ['claims_with_dissent']}")
    print(f"   process revisions: {len(pr['claim_verdicts_revised'])} verdict, "
          f"{len(pr['conflicts_reclassified'])} conflict reclassifications, "
          f"{len(pr['wording_revisions'])} wording; "
          f"{len(pr['claims_fully_rejected'])} fully rejected")
    for cid, c in summ["contradictions"].items():
        print(f"   {cid}: {c['reviewed_classification']} "
              f"(upheld_as_structural={c['upheld_as_structural']})")
    print(f"   overall attestation: {summ['overall_attestation']}")

    if args.ledger:
        ledger_cls = _load_layer9_ledger()
        if ledger_cls is None:
            print("[--ledger unavailable] desi_router/ledger.py not found — run from a checkout.")
            return 2
        led = ledger_cls(args.ledger, instance_id="marcognity_doktores_audit")
        rec = led.record("doktores_audit_run", summ)
        ok = led.verify_chain()
        print(f"   ledger: appended seq #{rec['seq']} (chain intact: {ok}) -> {args.ledger}")
        led.close()

    if args.print_summary:
        print(json.dumps(summ, ensure_ascii=False, indent=2, sort_keys=True))

    # A failed audit must never masquerade as a successful confirmation.
    if summ["overall_attestation"] in (AttestationRating.FAILED.value,
                                       AttestationRating.NEEDS_REVISION.value):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

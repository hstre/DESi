"""DES upstream  ->  DESi trajectory translator.

Upstream DES state schema (from `hstre/DES`):

    {
      "claims": {<claim_id>: {id, subject, predicate, object, status,
                              confidence, modality, evidence_refs,
                              scope, qualifier, ...}, ...},
      "operation_history": ["T3 on C001", "T4 on C001", ...],
      "discarded_hypotheses": [...],
      "weak_candidates": [...],
      "reframing_count": int,
      "iteration": int,
      "focus_claim_id": str,
      "anti_delphi_activations": int,
      "roles_generated": [...]
    }

DESi trajectory schema (from `src/desi/trajectory_loader.py`):

    {
      "trajectory_id": str,
      "domain": str | None,
      "seed": str | None,
      "persona": str | None,
      "steps": [{loop_index, focus_claim_id, operator, novel_claims,
                 dup_rate, failure_mode, claims}, ...],
      "en_events": [{loop_index, persona, eni_novelty, eni_non_drift,
                     eni_admissibility, admitted, novel_claims_next,
                     dup_rate_before, dup_rate_after}, ...],
      "terminal_failure_mode": str | None
    }

The schemas DO NOT match. Specifically, upstream DES has no native
field corresponding to:

  - novel_claims (per loop)
  - dup_rate (per loop)
  - any ENI metric
  - any per-loop failure_mode
  - any terminal_failure_mode flag

DESi WAS DESIGNED to consume hand-authored fixtures pre-populated with
these fields. Real DES output does not contain them.

Two translation modes are provided:

A) CONSERVATIVE: emit only fields recoverable from upstream DES.
   novel_claims = 0, dup_rate = 0.0, en_events = []. Honest about
   what the input does and does not contain.

B) HEURISTIC: synthesize approximations from operation_history
   patterns. Each synthesis is documented inline. The resulting
   trajectory is NOT real DES data; it is a best-effort
   reconstruction. This mode exists to show what DESi WOULD say
   if it had real data — recognising that the data is fabricated
   by the translator.

Usage:
    python3 translator.py path/to/des_state.json --mode conservative
                                                 --out out.json
    python3 translator.py path/to/des_state.json --mode heuristic
                                                 --out out.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys


OP_PATTERN = re.compile(r"^(T\d)\s+on\s+(\S+)$")


def parse_operation(op_str: str) -> tuple[str, str] | None:
    """Parse 'T3 on C001' -> ('T3', 'C001'). Returns None if unparseable."""
    m = OP_PATTERN.match(op_str.strip())
    if not m:
        return None
    return m.group(1), m.group(2)


def translate_conservative(des: dict, source_id: str) -> dict:
    """Honest, impoverished translation. Records what we know; leaves
    DESi-side metrics at their identity values.
    """
    ops = des.get("operation_history", [])
    steps = []
    for i, op_str in enumerate(ops):
        parsed = parse_operation(op_str)
        if parsed is None:
            operator = "UNKNOWN"
            focus = des.get("focus_claim_id") or "C001"
        else:
            operator, focus = parsed
        steps.append({
            "loop_index": i,
            "focus_claim_id": focus,
            "operator": operator,
            "novel_claims": 0,  # NOT IN UPSTREAM DES
            "dup_rate": 0.0,    # NOT IN UPSTREAM DES
            "failure_mode": None,
            "claims": [],       # snapshots per-iteration not in upstream state
        })
    return {
        "trajectory_id": f"des_upstream_{source_id}_conservative",
        "domain": "real_des_run",
        "seed": "upstream_DES_state",
        "persona": "DES_scheduler",
        "steps": steps,
        "en_events": [],         # upstream DES emits no ENI events
        "terminal_failure_mode": None,
        "_provenance": {
            "source": "hstre/DES des_state.json",
            "translation_mode": "conservative",
            "novel_claims_source": "ZEROED (not derivable from upstream state)",
            "dup_rate_source": "ZEROED (not derivable from upstream state)",
            "en_events_source": "EMPTY (upstream DES does not emit ENI)",
            "claims_per_step": "EMPTY (no per-iteration snapshots in upstream state)",
            "upstream_iteration": des.get("iteration"),
            "upstream_focus": des.get("focus_claim_id"),
            "upstream_claim_count": len(des.get("claims", {})),
            "upstream_op_count": len(ops),
        },
    }


def translate_heuristic(des: dict, source_id: str) -> dict:
    """Best-effort approximation. Synthesises novel_claims and dup_rate
    from operation_history patterns. All synthetic fields documented in
    _provenance.

    Heuristics (declared so they can be falsified):

    H1) novel_claims for step i = number of distinct focus_claim_ids
        encountered in operation_history[0..i] that did not appear in
        operation_history[0..i-1]. Approximates "did DES introduce a
        new claim this step?".

    H2) dup_rate for step i = (count of operator==same as step i-1 in
        previous 3 steps) / 3. Approximates "is DES repeating itself?".

    H3) en_events: synthesise an "EN" at each step where operator is
        T8 or T9 (DES's anti-delphi / synthesis operators).
        eni_novelty = 0.20 (placeholder high), or 0.08 (placeholder
        low) when the operator repeats from the previous step.

    None of H1-H3 reflect real DES measurements. They are NAMED
    heuristics so anyone reading this can disagree.
    """
    ops = des.get("operation_history", [])
    parsed = [parse_operation(o) or ("UNKNOWN", "C001") for o in ops]
    operators = [p[0] for p in parsed]
    focuses = [p[1] for p in parsed]

    # H1: novel_claims
    novel = []
    seen: set[str] = set()
    for f in focuses:
        if f in seen:
            novel.append(0)
        else:
            novel.append(1)
            seen.add(f)

    # H2: dup_rate
    dup = []
    for i in range(len(operators)):
        if i == 0:
            dup.append(0.0)
        else:
            window = operators[max(0, i - 3):i]
            same = sum(1 for o in window if o == operators[i])
            dup.append(round(same / max(1, len(window)), 3))

    steps = []
    for i in range(len(operators)):
        steps.append({
            "loop_index": i,
            "focus_claim_id": focuses[i],
            "operator": operators[i],
            "novel_claims": novel[i],
            "dup_rate": dup[i],
            "failure_mode": None,
            "claims": [],
        })

    # H3: synthetic EN events at T8 / T9 operations
    en_events = []
    for i, op in enumerate(operators):
        if op in ("T8", "T9"):
            prev_op = operators[i - 1] if i > 0 else None
            eni = 0.08 if op == prev_op else 0.20
            dup_before = dup[i]
            dup_after = dup[i + 1] if i + 1 < len(dup) else dup[i]
            novel_next = novel[i + 1] if i + 1 < len(novel) else 0
            en_events.append({
                "loop_index": i,
                "persona": "synthetic_EN",
                "eni_novelty": eni,
                "eni_non_drift": 0.5,
                "eni_admissibility": 1.0,
                "admitted": True,
                "novel_claims_next": novel_next,
                "dup_rate_before": dup_before,
                "dup_rate_after": dup_after,
            })

    return {
        "trajectory_id": f"des_upstream_{source_id}_heuristic",
        "domain": "real_des_run_heuristic",
        "seed": "upstream_DES_state",
        "persona": "DES_scheduler",
        "steps": steps,
        "en_events": en_events,
        "terminal_failure_mode": None,
        "_provenance": {
            "source": "hstre/DES des_state.json",
            "translation_mode": "heuristic",
            "novel_claims_source": "H1: 1 iff focus_claim_id is new at this step",
            "dup_rate_source": "H2: fraction of operator==same as current in previous 3 steps",
            "en_events_source": "H3: synthesise EN at T8 or T9 op; eni=0.08 if op repeats else 0.20",
            "heuristics_warning": (
                "These fields are NOT real DES measurements. They are translator"
                " heuristics named H1, H2, H3. Any DESi diagnosis from this"
                " trajectory reflects DESi reading my heuristics, not reading DES."
            ),
            "upstream_iteration": des.get("iteration"),
            "upstream_focus": des.get("focus_claim_id"),
            "upstream_claim_count": len(des.get("claims", {})),
            "upstream_op_count": len(ops),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="path to upstream des_state.json")
    ap.add_argument("--mode", choices=("conservative", "heuristic"), required=True)
    ap.add_argument("--source-id", default="state", help="suffix for trajectory_id")
    ap.add_argument("--out", required=True, help="output DESi trajectory json")
    args = ap.parse_args()

    des = json.loads(pathlib.Path(args.source).read_text())
    if args.mode == "conservative":
        traj = translate_conservative(des, args.source_id)
    else:
        traj = translate_heuristic(des, args.source_id)

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(traj, indent=2))
    print(f"wrote {out_path} (mode={args.mode}, steps={len(traj['steps'])}, ens={len(traj['en_events'])})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
import sys


# Fix 2 (external-reality challenge): use the canonical operator parser
# instead of a translator-local regex that only handled 'Tn on Cxxx'.
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from desi.operator_parser import (  # noqa: E402
    parse_des_operation, ParsedOperation, OperatorParseFailure,
    OPERATOR_PARSE_FAILURE,
)


def translate_conservative(des: dict, source_id: str) -> dict:
    """Honest, impoverished translation.

    Fix 1 (external-reality challenge): steps do NOT include
    `novel_claims` or `dup_rate` keys at all. DESi's
    `TrajectoryStep._normalise` records them as missing-metrics, and
    `validate_step_metric_coherence` will skip the dup<0.05/novel=0
    rule for these steps. Pre-fix the translator emitted explicit 0
    values which DESi could not distinguish from "deliberately zero".

    Fix 2: uses `parse_des_operation` which handles both
    `T3 on C001` and `T6[hypothesis_builder] on C003 -> C008`.
    Failures emit `OPERATOR_PARSE_FAILURE`, NOT `UNKNOWN`. Focus
    falls back to the empty string when source_claim cannot be
    recovered — there is no silent substitution of the upstream
    global focus_claim_id.

    Fix 3: trajectory carries `input_origin = "translated_DES_conservative"`.
    `render_report` will prepend the translator-derived disclaimer.
    """
    ops = des.get("operation_history", [])
    steps = []
    parse_failures = 0
    for i, op_str in enumerate(ops):
        parsed = parse_des_operation(op_str)
        if isinstance(parsed, OperatorParseFailure):
            operator = OPERATOR_PARSE_FAILURE
            focus = ""
            sub_role = None
            target = None
            parse_failures += 1
        else:
            operator = parsed.operator
            focus = parsed.source_claim
            sub_role = parsed.sub_role
            target = parsed.target_claim
        step: dict = {
            "loop_index": i,
            "focus_claim_id": focus,
            "operator": operator,
            "operator_sub_role": sub_role,
            "operator_target": target,
            "failure_mode": None,
            "claims": [],
            # novel_claims and dup_rate intentionally omitted — DESi's
            # model_validator will record them as missing.
        }
        steps.append(step)
    return {
        "trajectory_id": f"des_upstream_{source_id}_conservative",
        "domain": "real_des_run",
        "seed": "upstream_DES_state",
        "persona": "DES_scheduler",
        "steps": steps,
        "en_events": [],         # upstream DES emits no ENI events
        "terminal_failure_mode": None,
        "input_origin": "translated_DES_conservative",
        "_provenance": {
            "source": "hstre/DES des_state.json",
            "translation_mode": "conservative",
            "novel_claims_source": "OMITTED (recorded as missing by DESi)",
            "dup_rate_source": "OMITTED (recorded as missing by DESi)",
            "en_events_source": "EMPTY (upstream DES does not emit ENI)",
            "claims_per_step": "EMPTY (no per-iteration snapshots in upstream state)",
            "operator_parse_failures": parse_failures,
            "operator_failure_token": OPERATOR_PARSE_FAILURE,
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
    # Fix 2: explicit-failure parse; OPERATOR_PARSE_FAILURE token for
    # unparseable strings (no UNKNOWN silent substitution); empty source
    # claim when not recoverable (no default-focus inheritance).
    # EN-reconstruction cycle 1: also capture sub_role and target_claim.
    parsed_list: list = []
    parse_failures = 0
    for o in ops:
        r = parse_des_operation(o)
        if isinstance(r, OperatorParseFailure):
            parsed_list.append((OPERATOR_PARSE_FAILURE, "", None, None))
            parse_failures += 1
        else:
            parsed_list.append((r.operator, r.source_claim, r.sub_role, r.target_claim))
    operators = [p[0] for p in parsed_list]
    focuses = [p[1] for p in parsed_list]
    sub_roles = [p[2] for p in parsed_list]
    targets = [p[3] for p in parsed_list]

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
            "operator_sub_role": sub_roles[i],
            "operator_target": targets[i],
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
        # Fix 3: declared origin so render_report prepends the
        # translator-derived disclaimer.
        "input_origin": "translator_heuristic",
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
            "operator_parse_failures": parse_failures,
            "operator_failure_token": OPERATOR_PARSE_FAILURE,
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

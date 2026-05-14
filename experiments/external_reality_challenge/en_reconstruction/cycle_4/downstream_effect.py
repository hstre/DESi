"""Cycle-4 downstream-effect validator for reconstruction candidates.

Standalone analyser. No DESi-side changes. Uses ONLY native DES
fields from upstream des_state.json:

    operation_history  — list of operation strings
    claims             — dict of final claims (for survival check)
    focus_claim_id     — final focus (for terminal-anchor check)

For each created claim (target of a hypothesis_builder or falsifier
op with target), computes:

    first_focus_after_creation     int | None
    touch_count_after_creation     int
    survives_in_final_claims       bool
    is_terminal_focus              bool
    classification                 productive / dormant / terminal_anchor

NO ENI SCORES are invented. The classification is structural.

Usage:
    PYTHONPATH=src python3 \\
      experiments/external_reality_challenge/en_reconstruction/cycle_4/downstream_effect.py \\
      experiments/external_reality_challenge/source/des_state.json
"""
from __future__ import annotations

import json
import pathlib
import sys
from dataclasses import dataclass

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from desi.operator_parser import parse_des_operation, OperatorParseFailure  # noqa: E402


# Parameter — documented in proposal.md, not a DESi-side constant.
PRODUCTIVE_MIN_TOUCHES = 3


@dataclass(frozen=True)
class ParsedOp:
    loop: int
    raw: str
    operator: str
    sub_role: str | None
    source: str | None
    target: str | None


@dataclass(frozen=True)
class CandidateEffect:
    loop_created: int
    claim_id: str
    via_sub_role: str       # hypothesis_builder or falsifier
    via_operator: str
    source_at_creation: str | None
    first_focus_after_creation: int | None
    touch_count_after_creation: int
    survives_in_final_claims: bool
    is_terminal_focus: bool
    classification: str     # productive | dormant | terminal_anchor


def parse_all(operation_history: list[str]) -> list[ParsedOp]:
    out: list[ParsedOp] = []
    for i, op_str in enumerate(operation_history):
        r = parse_des_operation(op_str)
        if isinstance(r, OperatorParseFailure):
            out.append(ParsedOp(i, op_str, "OPERATOR_PARSE_FAILURE",
                                None, None, None))
        else:
            out.append(ParsedOp(i, op_str, r.operator, r.sub_role,
                                r.source_claim, r.target_claim))
    return out


def find_creation_candidates(parsed: list[ParsedOp]) -> list[ParsedOp]:
    """Operations that create a new target claim via hypothesis_builder
    or falsifier sub-role (cycles 1 + 2 reconstruction shapes)."""
    return [
        op for op in parsed
        if op.sub_role in {"hypothesis_builder", "falsifier"}
        and op.target is not None
    ]


def compute_effect(
    creation_op: ParsedOp,
    all_ops: list[ParsedOp],
    final_claims: dict,
    final_focus: str | None,
) -> CandidateEffect:
    claim = creation_op.target
    after = [op for op in all_ops if op.loop > creation_op.loop]
    # First focus: smallest loop where this claim is the source
    # (DES makes it the operand of a subsequent operation).
    first_focus: int | None = None
    for op in after:
        if op.source == claim:
            first_focus = op.loop
            break
    # Touch count: any post-creation op where claim appears as source
    # OR as target.
    touches = sum(
        1 for op in after
        if op.source == claim or op.target == claim
    )
    survives = claim in final_claims
    is_terminal = (claim == final_focus) if final_focus else False
    # Classification (mutually exclusive).
    if is_terminal:
        classification = "terminal_anchor"
    elif touches >= PRODUCTIVE_MIN_TOUCHES and survives:
        classification = "productive"
    else:
        classification = "dormant"
    return CandidateEffect(
        loop_created=creation_op.loop,
        claim_id=claim,
        via_sub_role=creation_op.sub_role,
        via_operator=creation_op.operator,
        source_at_creation=creation_op.source,
        first_focus_after_creation=first_focus,
        touch_count_after_creation=touches,
        survives_in_final_claims=survives,
        is_terminal_focus=is_terminal,
        classification=classification,
    )


def render_markdown(des_path: pathlib.Path, effects: list[CandidateEffect]) -> str:
    by_class: dict[str, int] = {}
    for e in effects:
        by_class[e.classification] = by_class.get(e.classification, 0) + 1
    lines: list[str] = []
    lines.append("# Cycle 4 — downstream-effect validation report")
    lines.append("")
    lines.append(f"**Source**: `{des_path}`")
    lines.append(f"**Candidates analysed**: {len(effects)}")
    lines.append(f"**Threshold** (PRODUCTIVE_MIN_TOUCHES): {PRODUCTIVE_MIN_TOUCHES}")
    lines.append("")
    lines.append("## Classification summary")
    lines.append("")
    lines.append("| Class | Count |")
    lines.append("|---|---:|")
    for c in ("productive", "dormant", "terminal_anchor"):
        lines.append(f"| `{c}` | {by_class.get(c, 0)} |")
    lines.append(f"| **TOTAL** | **{len(effects)}** |")
    lines.append("")
    lines.append("## Per-candidate downstream effect")
    lines.append("")
    lines.append(
        "| Claim | Created @ loop | Via | First focus after | Touches "
        "| Survives | Terminal focus | Classification |"
    )
    lines.append(
        "|---|---:|---|---:|---:|:---:|:---:|---|"
    )
    for e in sorted(effects, key=lambda x: x.loop_created):
        first_focus = (
            str(e.first_focus_after_creation)
            if e.first_focus_after_creation is not None
            else "—"
        )
        lines.append(
            f"| `{e.claim_id}` "
            f"| {e.loop_created} "
            f"| `{e.via_operator}[{e.via_sub_role}]` "
            f"| {first_focus} "
            f"| {e.touch_count_after_creation} "
            f"| {'✓' if e.survives_in_final_claims else '✗'} "
            f"| {'✓' if e.is_terminal_focus else '✗'} "
            f"| `{e.classification}` |"
        )
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append("- A **touch** is any post-creation operation where the "
                 "claim appears as either source or target.")
    lines.append("- **First focus after creation** is the smallest loop "
                 "index > creation_loop where source_claim == this claim.")
    lines.append("- **Survives** = present in upstream `claims` dict at "
                 "final state.")
    lines.append("- **Terminal focus** = equal to upstream `focus_claim_id` "
                 "at final state.")
    lines.append("- **Classification** is mutually exclusive. "
                 "`terminal_anchor` takes precedence over `productive`.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: downstream_effect.py <path/to/des_state.json>",
              file=sys.stderr)
        return 2
    des_path = pathlib.Path(sys.argv[1])
    des = json.loads(des_path.read_text())
    ops_raw = des.get("operation_history", [])
    final_claims = des.get("claims", {})
    final_focus = des.get("focus_claim_id")
    parsed = parse_all(ops_raw)
    creations = find_creation_candidates(parsed)
    effects = [
        compute_effect(op, parsed, final_claims, final_focus)
        for op in creations
    ]
    print(render_markdown(des_path, effects))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

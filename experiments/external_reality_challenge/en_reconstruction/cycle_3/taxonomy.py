"""Cycle-3 native-DES operation taxonomy classifier.

Documentation-only. No new detectors. Classifies each entry of
upstream `operation_history` into one of five categories:

    reconstructed_EN_candidate
    reconstructed_critique_navigation_candidate
    plain_operator_transition
    unsupported_extension
    unparsed_operation

Emits a markdown report on stdout.

Usage:
    PYTHONPATH=src python3 experiments/external_reality_challenge/en_reconstruction/cycle_3/taxonomy.py \\
        experiments/external_reality_challenge/source/des_state.json
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from desi.operator_parser import (  # noqa: E402
    parse_des_operation, OperatorParseFailure,
)


CATEGORIES = [
    "reconstructed_EN_candidate",
    "reconstructed_critique_navigation_candidate",
    "plain_operator_transition",
    "unsupported_extension",
    "unparsed_operation",
]

# These two must stay in sync with src/desi/diagnostics.py:
#   reconstruct_en_candidates -> "hypothesis_builder"
#   reconstruct_critique_navigation_candidates -> "falsifier"
EN_SUB_ROLE = "hypothesis_builder"
CN_SUB_ROLE = "falsifier"
KNOWN_SUB_ROLES = {EN_SUB_ROLE, CN_SUB_ROLE}


def classify(raw_op: str) -> tuple[str, dict]:
    """Return (category, detail) for one operation_history string."""
    parsed = parse_des_operation(raw_op)
    if isinstance(parsed, OperatorParseFailure):
        return "unparsed_operation", {
            "raw": raw_op,
            "operator": "OPERATOR_PARSE_FAILURE",
            "sub_role": None,
            "source": None,
            "target": None,
        }
    detail = {
        "raw": raw_op,
        "operator": parsed.operator,
        "sub_role": parsed.sub_role,
        "source": parsed.source_claim,
        "target": parsed.target_claim,
    }
    # Parse succeeded — apply the two known reconstruction rules.
    if parsed.sub_role == EN_SUB_ROLE and parsed.target_claim is not None:
        return "reconstructed_EN_candidate", detail
    if parsed.sub_role == CN_SUB_ROLE and parsed.target_claim is not None:
        return "reconstructed_critique_navigation_candidate", detail
    # Anything with a sub-role we don't recognise, OR a target without a
    # sub-role, lands in unsupported_extension. Future cycles can decide
    # whether to add a rule for these shapes.
    if parsed.sub_role is not None and parsed.sub_role not in KNOWN_SUB_ROLES:
        return "unsupported_extension", detail
    if parsed.sub_role is None and parsed.target_claim is not None:
        return "unsupported_extension", detail
    # Default: bare Tn op on existing claim.
    return "plain_operator_transition", detail


def classify_all(operation_history: list[str]) -> list[tuple[int, str, dict]]:
    return [(i, *classify(op)) for i, op in enumerate(operation_history)]


def render_markdown(des_state_path: pathlib.Path, classifications) -> str:
    counts = {c: 0 for c in CATEGORIES}
    target_creators_in_known = 0
    target_creators_total = 0
    for _, cat, det in classifications:
        counts[cat] += 1
        if det.get("target"):
            target_creators_total += 1
            if cat in {
                "reconstructed_EN_candidate",
                "reconstructed_critique_navigation_candidate",
            }:
                target_creators_in_known += 1

    n = len(classifications)
    coverage_reconstructed = (
        counts["reconstructed_EN_candidate"]
        + counts["reconstructed_critique_navigation_candidate"]
    )
    lines: list[str] = []
    lines.append("# Cycle 3 — native-DES operation taxonomy report")
    lines.append("")
    lines.append(f"**Source**: `{des_state_path}`")
    lines.append(f"**Total operations**: {n}")
    lines.append("")
    lines.append("## Per-category counts")
    lines.append("")
    lines.append("| Category | Count | % |")
    lines.append("|---|---:|---:|")
    for c in CATEGORIES:
        pct = (counts[c] / n * 100) if n else 0
        lines.append(f"| `{c}` | {counts[c]} | {pct:.1f}% |")
    lines.append(f"| **TOTAL** | **{n}** | **100.0%** |")
    lines.append("")
    lines.append("## Coverage measurements")
    lines.append("")
    lines.append(f"- **coverage (reconstructed / total)**: "
                 f"{coverage_reconstructed} / {n} "
                 f"= {coverage_reconstructed / n * 100:.1f}%")
    lines.append(f"- **unparsed rate**: "
                 f"{counts['unparsed_operation']} / {n} "
                 f"= {counts['unparsed_operation'] / n * 100:.1f}%")
    lines.append(f"- **unsupported rate** (parsed but no reconstruction rule): "
                 f"{counts['unsupported_extension']} / {n} "
                 f"= {counts['unsupported_extension'] / n * 100:.1f}%")
    if target_creators_total:
        completeness = target_creators_in_known / target_creators_total * 100
    else:
        completeness = 100.0
    lines.append(
        f"- **target-creating completeness**: "
        f"{target_creators_in_known} / {target_creators_total} "
        f"target-creating ops landed in a reconstruction category "
        f"= {completeness:.1f}%"
    )
    lines.append("")
    lines.append("## Per-operation classification (n=" + str(n) + ")")
    lines.append("")
    lines.append("| Loop | Category | Operator | Sub-role | Source | Target | Raw |")
    lines.append("|---:|---|---|---|---|---|---|")
    for i, cat, det in classifications:
        lines.append(
            f"| {i} "
            f"| `{cat}` "
            f"| `{det['operator']}` "
            f"| `{det['sub_role'] or '-'}` "
            f"| `{det['source'] or '-'}` "
            f"| `{det['target'] or '-'}` "
            f"| `{det['raw']}` |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: taxonomy.py <path/to/des_state.json>", file=sys.stderr)
        return 2
    des_state_path = pathlib.Path(sys.argv[1])
    des = json.loads(des_state_path.read_text())
    ops = des.get("operation_history", [])
    classifications = classify_all(ops)
    print(render_markdown(des_state_path, classifications))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

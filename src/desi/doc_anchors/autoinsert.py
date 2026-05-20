"""Auto-anchor proposer — Aufgabe 4.

For a markdown document this module proposes inline
``[claim-anchor: ...]`` insertions for *unambiguous* numeric and
hash claims: a candidate fires iff exactly one (artifact, field)
pair in ``artifacts/`` carries the claim's value at the claim's
key. Ambiguous matches are left untouched.

The module is pure — it never writes to disk. Callers decide
whether to persist the proposed edits.
"""
from __future__ import annotations

import json
import pathlib
import re
from dataclasses import dataclass
from typing import Any

from .schema import ANCHOR_PREFIX


_HEX16 = re.compile(r"\b([0-9a-f]{16})\b")
_DECIMAL = re.compile(r"-?\d+(?:\.\d+)?")


_NUMERIC_KEYS: frozenset[str] = frozenset({
    "precision", "recall", "rule_hit_rate", "no_rule_match_rate",
    "false_positives", "multistep_trigger_rate",
    "main_trigger_rate", "known_false_positive_reopen_rate",
    "authority_touch_rate", "philosophy_touch_rate",
    "metaphor_touch_rate", "recursion_reach_rate",
    "bridge_creation_rate", "consilium_call_rate",
    "resolver_entry_rate", "false_depth_zero_rate",
    "cycle_detection_rate", "blocked_propagation_accuracy",
    "best_fitness", "best_depth", "r2_r3_gain_count",
    "r4_regression_count", "r5_regression_count",
    "actionable_deficits", "non_actionable_deficits",
    "highest_severity", "highest_confidence",
    "accepted_steps", "rejected_steps", "killed_steps",
    "total_cases", "total_steps", "total_deficits",
    "safe_candidate_rate", "multi_hop_case_coverage",
    "parser_vs_rule_misclassification_rate",
    "self_deception_rate", "total_claims", "verified_claims",
})


@dataclass(frozen=True)
class AnchorProposal:
    doc_path: str
    line_number: int
    line_text: str
    anchor_text: str
    artifact: str
    field: str
    expected: str


def _load_artifacts(
    repo_root: pathlib.Path,
) -> dict[str, Any]:
    """Map ``artifacts/<rel>`` → parsed JSON payload."""
    out: dict[str, Any] = {}
    art_root = repo_root / "artifacts"
    if not art_root.exists():
        return out
    for p in sorted(art_root.rglob("*.json")):
        try:
            out[p.relative_to(repo_root).as_posix()] = json.loads(
                p.read_text()
            )
        except json.JSONDecodeError:
            continue
    return out


def _walk_paths(
    obj: Any, prefix: str = "",
) -> list[tuple[str, Any]]:
    """Yield ``(dotted_path, value)`` for every leaf in ``obj``."""
    out: list[tuple[str, Any]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_prefix = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)):
                out.extend(_walk_paths(v, new_prefix))
            else:
                out.append((new_prefix, v))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            new_prefix = f"{prefix}.[{i}]"
            if isinstance(v, (dict, list)):
                out.extend(_walk_paths(v, new_prefix))
            else:
                out.append((new_prefix, v))
    return out


def _candidate_hex_anchors(
    artifacts: dict[str, Any],
) -> dict[str, list[tuple[str, str]]]:
    """``hex_value → [(artifact_rel, field_path), ...]``."""
    out: dict[str, list[tuple[str, str]]] = {}
    for rel, payload in artifacts.items():
        for path, value in _walk_paths(payload):
            if isinstance(value, str) and _HEX16.fullmatch(value):
                out.setdefault(value, []).append((rel, path))
    return out


def _approx(a: Any, b: float) -> bool:
    try:
        return abs(float(a) - b) < 1e-4
    except (TypeError, ValueError):
        return False


def propose_anchors(
    *,
    doc_path: str,
    text: str,
    repo_root: pathlib.Path,
) -> tuple[AnchorProposal, ...]:
    artifacts = _load_artifacts(repo_root)
    hex_index = _candidate_hex_anchors(artifacts)

    proposals: list[AnchorProposal] = []
    for n, line in enumerate(text.splitlines(), start=1):
        if not line.strip() or ANCHOR_PREFIX in line:
            continue
        # 1. Hash candidates.
        for m in _HEX16.finditer(line):
            hexv = m.group(1)
            if hexv.isdigit():
                continue
            matches = hex_index.get(hexv, [])
            if len(matches) == 1:
                art, field = matches[0]
                proposals.append(AnchorProposal(
                    doc_path=doc_path, line_number=n,
                    line_text=line,
                    anchor_text=(
                        f"[claim-anchor: artifact={art}, "
                        f"field={field}, expected={hexv}]"
                    ),
                    artifact=art, field=field, expected=hexv,
                ))
                # Only one anchor per hex value per line.
                break
        # 2. Numeric candidates.
        low = line.lower()
        for key in _NUMERIC_KEYS:
            if key not in low:
                continue
            idx = low.find(key)
            tail = line[idx + len(key):]
            m = _DECIMAL.search(tail)
            if not m:
                continue
            value_str = m.group(0)
            try:
                value = float(value_str)
            except ValueError:
                continue
            # Find unique (artifact, field) carrying this key+value.
            hits: list[tuple[str, str]] = []
            for rel, payload in artifacts.items():
                for path, art_value in _walk_paths(payload):
                    if not path.endswith(key):
                        continue
                    if _approx(art_value, value):
                        hits.append((rel, path))
            if len(hits) == 1:
                art, field = hits[0]
                proposals.append(AnchorProposal(
                    doc_path=doc_path, line_number=n,
                    line_text=line,
                    anchor_text=(
                        f"[claim-anchor: artifact={art}, "
                        f"field={field}, expected={value_str}]"
                    ),
                    artifact=art, field=field, expected=value_str,
                ))
                break   # one numeric anchor per line is enough
    return tuple(proposals)


def apply_proposals(
    text: str,
    proposals: tuple[AnchorProposal, ...],
) -> str:
    """Insert each anchor at the end of its source line."""
    if not proposals:
        return text
    by_line: dict[int, AnchorProposal] = {p.line_number: p for p in proposals}
    out_lines: list[str] = []
    for n, line in enumerate(text.splitlines(), start=1):
        if n in by_line and by_line[n].anchor_text not in line:
            line = f"{line}  {by_line[n].anchor_text}"
        out_lines.append(line)
    # Preserve trailing newline.
    suffix = "\n" if text.endswith("\n") else ""
    return "\n".join(out_lines) + suffix


__all__ = ["AnchorProposal", "apply_proposals", "propose_anchors"]

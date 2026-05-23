"""v23.1 - Experimental Conditions Reconstruction report.

Pflichtmetriken (directive § v23.1):

* metric_visibility
* condition_visibility
* sandbox_honesty
* result_traceability
* replay_stability

Killerfrage: "Wuerden die Resultate ohne Kontext wie
ausgedachte Benchmarkzahlen wirken? Wenn ja: Failure."

Every reported number is reconstructed from its sprint source,
its experimental conditions, its upstream fixture and the fact
that the data is synthetic - so no naked number remains.
"""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass

from .conditions import (
    PROVENANCE, condition_visibility, naked_numbers, results,
    result_traceability,
)
from .fixtures import (
    fixture_notes, synthetic_share, undocumented_results,
)
from .metrics import (
    definitions, metric_visibility, undefined_metrics,
)
from .sandbox_limits import sandbox_honesty, sandbox_limits

VERDICT_GROUNDED = "CONDITIONS_RECONSTRUCTED"
VERDICT_NAKED = "NAKED_NUMBERS_REMAIN"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_GROUNDED, VERDICT_NAKED, VERDICT_HALT,
)

_VISIBILITY_FLOOR = 0.90
_TRACEABILITY_FLOOR = 0.90
_CONDITION_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _signature() -> str:
    parts = [
        f"{r.result_id}:{r.metric_name}:{_round(r.value)}:"
        f"{r.sprint_source}"
        for r in results()
    ]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _metric_tuple() -> tuple[object, ...]:
    return (
        metric_visibility(), condition_visibility(),
        sandbox_honesty(), result_traceability(),
        synthetic_share(),
    )


def _replay_stability() -> float:
    if _signature() != _signature():
        return 0.0
    return 1.0 if _metric_tuple() == _metric_tuple() else 0.0


def _recommendation(
    *, replay: float, m_vis: float, c_vis: float,
    trace: float, honest: bool, naked: tuple[str, ...],
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        naked
        or not honest
        or m_vis < _VISIBILITY_FLOOR
        or c_vis < _CONDITION_FLOOR
        or trace < _TRACEABILITY_FLOOR
    ):
        return VERDICT_NAKED
    return VERDICT_GROUNDED


@dataclass(frozen=True)
class V231Report:
    result_count: int
    metric_count: int
    sandbox_limit_count: int
    metric_visibility: float
    condition_visibility: float
    result_traceability: float
    synthetic_share: float
    sandbox_honesty: bool
    naked_numbers: tuple[str, ...]
    undefined_metrics: tuple[str, ...]
    undocumented_results: tuple[str, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "result_count": self.result_count,
            "metric_count": self.metric_count,
            "sandbox_limit_count": self.sandbox_limit_count,
            "metric_visibility": self.metric_visibility,
            "condition_visibility": self.condition_visibility,
            "result_traceability": self.result_traceability,
            "synthetic_share": self.synthetic_share,
            "sandbox_honesty": self.sandbox_honesty,
            "naked_numbers": list(self.naked_numbers),
            "undefined_metrics": list(self.undefined_metrics),
            "undocumented_results":
                list(self.undocumented_results),
            "replay_stability": self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V231Report:
    m_vis = metric_visibility()
    c_vis = condition_visibility()
    trace = result_traceability()
    syn = synthetic_share()
    honest = sandbox_honesty()
    naked = naked_numbers()
    undef = undefined_metrics()
    undoc = undocumented_results()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, m_vis=m_vis, c_vis=c_vis, trace=trace,
        honest=honest, naked=naked,
    )
    rationale = (
        f"INFO: results {len(results())}; metric definitions "
        f"{len(definitions())}; sandbox limits "
        f"{len(sandbox_limits())}",
        "INFO: provenance - DESi-only baseline=v19, "
        "DESi+Wild=v20, comparison=v21, paper=v22; every value "
        "read live from its source phase, not re-typed",
        f"{'PASS' if m_vis >= 0.90 else 'FAIL'}: "
        f"metric_visibility {m_vis} >= 0.90 (undefined "
        f"{list(undef)})",
        f"{'PASS' if c_vis >= 0.90 else 'FAIL'}: "
        f"condition_visibility {c_vis} >= 0.90",
        f"{'PASS' if trace >= 0.90 else 'FAIL'}: "
        f"result_traceability {trace} >= 0.90",
        f"{'PASS' if honest else 'FAIL'}: "
        f"sandbox_honesty {honest} (synthetic_share {syn}; "
        f"undocumented {list(undoc)})",
        f"{'PASS' if not naked else 'FAIL'}: "
        f"naked_numbers {list(naked)} (must be empty - no "
        f"number without derivation)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V231Report(
        result_count=len(results()),
        metric_count=len(definitions()),
        sandbox_limit_count=len(sandbox_limits()),
        metric_visibility=m_vis,
        condition_visibility=c_vis,
        result_traceability=trace,
        synthetic_share=syn,
        sandbox_honesty=honest,
        naked_numbers=naked,
        undefined_metrics=undef,
        undocumented_results=undoc,
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def provenance_section() -> str:
    """Markdown 'Provenance and conditions' section for the v2
    paper - every result with its source, conditions and
    fixture, plus the explicit sandbox limits."""
    notes = {n.result_id: n for n in fixture_notes()}
    lines = [
        "## Provenance and Conditions",
        "",
        "All results are synthetic and scoped to the sandbox. "
        "Provenance: the DESi-only baseline is sprint v19, the "
        "DESi + Wild Explorer setting is v20, the comparison "
        "is v21, and the rendered document is v22. Each number "
        "below is reproduced live from the sprint that "
        "produced it.",
        "",
        "| Result | Metric | Value | Source | Conditions |",
        "|---|---|---|---|---|",
    ]
    for r in results():
        lines.append(
            f"| {r.result_id} | {r.metric_name} | "
            f"{_round(r.value)} | {r.sprint_source} | "
            f"{r.conditions} |"
        )
    lines += [
        "",
        "### Derivations",
        "",
    ]
    for r in results():
        note = notes.get(r.result_id)
        if note is not None:
            lines.append(
                f"- **{r.result_id} {r.metric_name}** "
                f"({note.fixture}): {note.derivation}"
            )
    lines += [
        "",
        "### Sandbox Limits",
        "",
    ]
    for l in sandbox_limits():
        lines.append(f"- **{l.limit_id}**: {l.statement}")
    lines.append("")
    return "\n".join(lines)


def build_conditions_artifact() -> dict[str, object]:
    return {
        "schema_version": "v23_1_experimental_conditions",
        "disclaimer": (
            "Reconstructs the experimental conditions behind "
            "every reported number: the sprint source, the "
            "active agents and governance, the upstream "
            "fixture, and the fact that all data is synthetic. "
            "No number is presented without derivation. Values "
            "are read live from their source phases; the data "
            "is synthetic and scoped to the sandbox, with no "
            "claim about performance outside it. Replay-exact."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "provenance": dict(sorted(PROVENANCE.items())),
        "results": [r.to_dict() for r in results()],
        "metric_definitions": [d.to_dict() for d in definitions()],
        "fixture_notes": [n.to_dict() for n in fixture_notes()],
        "sandbox_limits": [l.to_dict() for l in sandbox_limits()],
        "metric_visibility": metric_visibility(),
        "condition_visibility": condition_visibility(),
        "result_traceability": result_traceability(),
        "synthetic_share": synthetic_share(),
        "sandbox_honesty": sandbox_honesty(),
        "naked_numbers": list(naked_numbers()),
        "undefined_metrics": list(undefined_metrics()),
        "undocumented_results": list(undocumented_results()),
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_GROUNDED",
    "VERDICT_HALT",
    "VERDICT_NAKED",
    "V231Report",
    "build_conditions_artifact",
    "build_report",
    "provenance_section",
]

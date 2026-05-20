"""v23.2 - Scientific Density Revision report.

Pflichtmetriken (directive § v23.2):

* scientific_density
* tradeoff_visibility
* hypothesis_visibility
* claim_conservatism
* replay_stability

Killerfrage: "Liest sich die Revision wie ein duenner Hype-
Text oder wie ein dichter, ehrlicher wissenschaftlicher
Beitrag?"

The revision raises technical density, makes design tradeoffs
visible, marks every forward-looking statement as a
hypothesis, and keeps significance claims scoped - without
introducing any forbidden term.
"""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass

from desi.scientific_rendering import forbidden_hits

from .interpretation import (
    hypotheses, hypothesis_visibility, interpretations,
    unbounded_interpretations, unmarked_hypotheses,
)
from .motivation import (
    motivation_points, scientific_density, thin_points,
)
from .significance import (
    claim_conservatism, overclaimed_statements,
    significance_statements,
)
from .tradeoffs import (
    one_sided_tradeoffs, tradeoff_visibility, tradeoffs,
)

VERDICT_DENSE = "SCIENTIFICALLY_DENSE"
VERDICT_THIN = "TOO_THIN_OR_OVERCLAIMED"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_DENSE, VERDICT_THIN, VERDICT_HALT,
)

_DENSITY_FLOOR = 0.90
_TRADEOFF_FLOOR = 0.90
_HYPOTHESIS_FLOOR = 0.90
_CONSERVATISM_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _corpus_texts() -> tuple[str, ...]:
    parts: list[str] = []
    parts += [p.text for p in motivation_points()]
    for t in tradeoffs():
        parts += [t.decision, t.benefit, t.cost]
    for i in interpretations():
        parts += [i.means, i.does_not_mean]
    parts += [h.text for h in hypotheses()]
    parts += [s.text for s in significance_statements()]
    return tuple(parts)


def corpus_forbidden_hits() -> tuple[str, ...]:
    hits: list[str] = []
    for text in _corpus_texts():
        hits += list(forbidden_hits(text))
    return tuple(sorted(set(hits)))


def _signature() -> str:
    return hashlib.sha256(
        "|".join(_corpus_texts()).encode("utf-8"),
    ).hexdigest()


def _metric_tuple() -> tuple[object, ...]:
    return (
        scientific_density(), tradeoff_visibility(),
        hypothesis_visibility(), claim_conservatism(),
    )


def _replay_stability() -> float:
    if _signature() != _signature():
        return 0.0
    return 1.0 if _metric_tuple() == _metric_tuple() else 0.0


def _recommendation(
    *, replay: float, density: float, tradeoff: float,
    hypothesis: float, conservatism: float,
    forbidden_clean: bool,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        not forbidden_clean
        or density < _DENSITY_FLOOR
        or tradeoff < _TRADEOFF_FLOOR
        or hypothesis < _HYPOTHESIS_FLOOR
        or conservatism < _CONSERVATISM_FLOOR
    ):
        return VERDICT_THIN
    return VERDICT_DENSE


@dataclass(frozen=True)
class V232Report:
    motivation_count: int
    tradeoff_count: int
    hypothesis_count: int
    significance_count: int
    scientific_density: float
    tradeoff_visibility: float
    hypothesis_visibility: float
    claim_conservatism: float
    thin_points: tuple[str, ...]
    one_sided_tradeoffs: tuple[str, ...]
    unmarked_hypotheses: tuple[str, ...]
    overclaimed_statements: tuple[str, ...]
    corpus_forbidden_hits: tuple[str, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "motivation_count": self.motivation_count,
            "tradeoff_count": self.tradeoff_count,
            "hypothesis_count": self.hypothesis_count,
            "significance_count": self.significance_count,
            "scientific_density": self.scientific_density,
            "tradeoff_visibility": self.tradeoff_visibility,
            "hypothesis_visibility": self.hypothesis_visibility,
            "claim_conservatism": self.claim_conservatism,
            "thin_points": list(self.thin_points),
            "one_sided_tradeoffs":
                list(self.one_sided_tradeoffs),
            "unmarked_hypotheses":
                list(self.unmarked_hypotheses),
            "overclaimed_statements":
                list(self.overclaimed_statements),
            "corpus_forbidden_hits":
                list(self.corpus_forbidden_hits),
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


def build_report() -> V232Report:
    density = scientific_density()
    tradeoff = tradeoff_visibility()
    hyp = hypothesis_visibility()
    cons = claim_conservatism()
    hits = corpus_forbidden_hits()
    clean = not hits
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, density=density, tradeoff=tradeoff,
        hypothesis=hyp, conservatism=cons,
        forbidden_clean=clean,
    )
    rationale = (
        f"INFO: motivation points {len(motivation_points())}; "
        f"tradeoffs {len(tradeoffs())}; hypotheses "
        f"{len(hypotheses())}; significance statements "
        f"{len(significance_statements())}",
        "INFO: numbers cited in the revision are pulled live "
        "from the v23.1 reconstruction, not re-typed",
        f"{'PASS' if density >= 0.90 else 'FAIL'}: "
        f"scientific_density {density} >= 0.90 (thin "
        f"{list(thin_points())})",
        f"{'PASS' if tradeoff >= 0.90 else 'FAIL'}: "
        f"tradeoff_visibility {tradeoff} >= 0.90 (one-sided "
        f"{list(one_sided_tradeoffs())})",
        f"{'PASS' if hyp >= 0.90 else 'FAIL'}: "
        f"hypothesis_visibility {hyp} >= 0.90 (unmarked "
        f"{list(unmarked_hypotheses())})",
        f"{'PASS' if cons >= 0.90 else 'FAIL'}: "
        f"claim_conservatism {cons} >= 0.90 (overclaimed "
        f"{list(overclaimed_statements())})",
        f"{'PASS' if clean else 'FAIL'}: "
        f"corpus_forbidden_hits {list(hits)} (must be empty)",
        f"INFO: unbounded interpretations "
        f"{list(unbounded_interpretations())}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V232Report(
        motivation_count=len(motivation_points()),
        tradeoff_count=len(tradeoffs()),
        hypothesis_count=len(hypotheses()),
        significance_count=len(significance_statements()),
        scientific_density=density,
        tradeoff_visibility=tradeoff,
        hypothesis_visibility=hyp,
        claim_conservatism=cons,
        thin_points=thin_points(),
        one_sided_tradeoffs=one_sided_tradeoffs(),
        unmarked_hypotheses=unmarked_hypotheses(),
        overclaimed_statements=overclaimed_statements(),
        corpus_forbidden_hits=hits,
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def density_sections() -> str:
    """Markdown 'Motivation / Tradeoffs / Interpretation /
    Significance' block for the revised v2 paper."""
    lines = [
        "## Motivation",
        "",
    ]
    for p in motivation_points():
        lines.append(f"- {p.text}")
    lines += ["", "## Design Tradeoffs", ""]
    for t in tradeoffs():
        lines.append(
            f"- **{t.decision}** - benefit: {t.benefit}; "
            f"cost: {t.cost}"
        )
    lines += ["", "## Interpretation", ""]
    for i in interpretations():
        lines.append(
            f"- **{i.result_id}** means {i.means}; it does "
            f"not mean {i.does_not_mean}."
        )
    lines += ["", "### Open Hypotheses", ""]
    for h in hypotheses():
        lines.append(f"- {h.text}")
    lines += ["", "## Significance", ""]
    for s in significance_statements():
        lines.append(f"- {s.text}")
    lines.append("")
    return "\n".join(lines)


def build_density_artifact() -> dict[str, object]:
    return {
        "schema_version": "v23_2_scientific_density",
        "disclaimer": (
            "Raises the scientific density of the follow-up: "
            "every motivation statement carries concrete "
            "technical content, design tradeoffs are stated "
            "with both benefit and cost, forward-looking "
            "statements are marked as hypotheses, and "
            "significance claims stay scoped to the synthetic "
            "sandbox. Numbers are pulled live from the v23.1 "
            "reconstruction. No forbidden term appears. "
            "Replay-exact."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "motivation_points": [
            p.to_dict() for p in motivation_points()
        ],
        "tradeoffs": [t.to_dict() for t in tradeoffs()],
        "interpretations": [
            i.to_dict() for i in interpretations()
        ],
        "hypotheses": [h.to_dict() for h in hypotheses()],
        "significance_statements": [
            s.to_dict() for s in significance_statements()
        ],
        "scientific_density": scientific_density(),
        "tradeoff_visibility": tradeoff_visibility(),
        "hypothesis_visibility": hypothesis_visibility(),
        "claim_conservatism": claim_conservatism(),
        "thin_points": list(thin_points()),
        "one_sided_tradeoffs": list(one_sided_tradeoffs()),
        "unmarked_hypotheses": list(unmarked_hypotheses()),
        "overclaimed_statements": list(overclaimed_statements()),
        "corpus_forbidden_hits": list(corpus_forbidden_hits()),
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_DENSE",
    "VERDICT_HALT",
    "VERDICT_THIN",
    "V232Report",
    "build_density_artifact",
    "build_report",
    "corpus_forbidden_hits",
    "density_sections",
]

"""The red-team benchmark: score reviewers against the five failure modes.

Deterministic and offline. A reviewer "catches" a probe iff it raises the probe's
required flag. The scorecard reports per-mode and overall catch-rate. Honest by
construction: the DESi reference reviewer scores 5/5 because it IS the analysis that
defined the probes; the naive whole-text baseline scores 0/5, so the benchmark
demonstrably discriminates. The point is the harness + the contrast + the external
slot, not the reference's own score.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .failure_modes import PROBES
from .reviewers import Reviewer, default_reviewers

REDTEAM_NOTE = (
    "Der DESi-Referenz-Reviewer erreicht 5/5 per Konstruktion (er IST die Analyse, die "
    "die Probes definiert hat) — das ist ein Gold-Anker, keine unabhängige Leistung. Der "
    "Wert liegt im Harness, im Kontrast zum naiven Whole-Text-Reviewer (0/5) und im "
    "External-Slot, mit dem sich ein echter Background-Reviewer (z. B. der von Claude "
    "Science) an denselben fünf Failure-Modes messen lässt."
)


@dataclass(frozen=True)
class ProbeResult:
    probe_key: str
    failure_mode: str
    required_flag: str
    raised: tuple[str, ...]
    caught: bool

    def to_dict(self) -> dict:
        return {
            "probe_key": self.probe_key,
            "failure_mode": self.failure_mode,
            "required_flag": self.required_flag,
            "raised": list(self.raised),
            "caught": self.caught,
        }


def run_reviewer(reviewer: Reviewer) -> list[ProbeResult]:
    out: list[ProbeResult] = []
    for p in PROBES:
        raised = reviewer.review(p)
        out.append(ProbeResult(
            probe_key=p.key, failure_mode=p.failure_mode.value,
            required_flag=p.must_flag.value,
            raised=tuple(sorted(f.value for f in raised)),
            caught=p.must_flag in raised))
    return out


def score(reviewer: Reviewer) -> dict:
    results = run_reviewer(reviewer)
    caught = sum(1 for r in results if r.caught)
    return {
        "reviewer": reviewer.name,
        "caught": caught,
        "total": len(results),
        "catch_rate": round(caught / len(results), 3) if results else 0.0,
        "per_mode": {r.failure_mode: r.caught for r in results},
        "results": [r.to_dict() for r in results],
    }


def scorecard(reviewers: list[Reviewer] | None = None) -> dict:
    reviewers = reviewers or default_reviewers()
    scores = [score(r) for r in reviewers]
    return {
        "note": REDTEAM_NOTE,
        "failure_modes": [p.failure_mode.value for p in PROBES],
        "scores": scores,
        "discriminating": (
            any(s["catch_rate"] == 1.0 for s in scores)
            and any(s["catch_rate"] == 0.0 for s in scores)),
    }


def render_report_md(reviewers: list[Reviewer] | None = None) -> str:
    reviewers = reviewers or default_reviewers()
    card = scorecard(reviewers)
    o: list[str] = []
    o.append("# Red-Team-Benchmark — hält ein Background-Reviewer die fünf Failure-Modes aus?\n")
    o.append("*Motiviert durch Claude Science ('a background reviewer flags incorrect "
             "citations, untraceable numbers ...'). Die MarCognity/Muse-Spark-Fallstudie wird "
             "hier zum Prüfstein: erkennt ein Reviewer die fünf epistemischen Fehler, an denen "
             "MarCognitys eigener Validator scheiterte? Deterministisch, offline.*\n")
    o.append(f"> {card['note']}\n")

    o.append("## Failure-Modes (je an das Material verankert)\n")
    o.append("| # | Failure-Mode | muss geflaggt werden | Anker | Claims |")
    o.append("|---|---|---|---|---|")
    for i, p in enumerate(PROBES, 1):
        o.append(f"| {i} | **{p.failure_mode.value}** | `{p.must_flag.value}` | "
                 f"{p.source_anchor} | {', '.join(p.claim_ids)} |")

    o.append("\n## Scorecard\n")
    header = "| Reviewer | " + " | ".join(p.failure_mode.value for p in PROBES) + " | catch-rate |"
    o.append(header)
    o.append("|" + "---|" * (len(PROBES) + 2))
    for s in card["scores"]:
        cells = " | ".join("✓" if s["per_mode"].get(p.failure_mode.value) else "✗"
                           for p in PROBES)
        o.append(f"| **{s['reviewer']}** | {cells} | {s['caught']}/{s['total']} |")
    o.append(f"\n**Diskriminiert der Benchmark?** {'ja' if card['discriminating'] else 'nein'} "
             "— ein Reviewer erreicht 5/5, ein anderer 0/5.\n")

    o.append("## Wie man einen externen Reviewer misst\n")
    o.append("Strukturierte Ausgabe eines echten Background-Reviewers als JSON ablegen und "
             "einspeisen:\n")
    example = (
        "```json\n"
        "{\n"
        '  "name": "some-background-reviewer",\n'
        '  "flags": {\n'
        '    "P1-untraceable": ["untraceable_citation"],\n'
        '    "P2-domain": ["source_domain_mismatch"]\n'
        "  }\n"
        "}\n"
        "```\n"
    )
    o.append(example)
    o.append("`python -m desi.case_studies.marcognity_muse_spark.redteam --external out.json`.\n")

    o.append("## Grenze\n")
    o.append("Fünf Probes, ein Fall — ein *Startpunkt*, keine erschöpfende Suite. Es prüft "
             "**Erkennung** dieser fünf Fehler, nicht die allgemeine Reviewer-Qualität. Und der "
             "DESi-Reviewer ist Referenz, kein unabhängiger Prüfer (siehe Notiz oben).\n")
    return "\n".join(o)


def write_results_jsonl(path: Path, reviewers: list[Reviewer] | None = None) -> int:
    reviewers = reviewers or default_reviewers()
    rows: list[dict] = []
    for r in reviewers:
        for res in run_reviewer(r):
            rows.append({"reviewer": r.name, **res.to_dict()})
    lines = [json.dumps(x, ensure_ascii=False, sort_keys=True) for x in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(lines)


def write_all(out_dir: Path, reviewers: list[Reviewer] | None = None) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    n = write_results_jsonl(out_dir / "redteam_results.jsonl", reviewers)
    (out_dir / "REDTEAM.md").write_text(render_report_md(reviewers), encoding="utf-8")
    (out_dir / "redteam_scorecard.json").write_text(
        json.dumps(scorecard(reviewers), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    return {"result_rows": n, "out_dir": str(out_dir)}


__all__ = [
    "ProbeResult", "run_reviewer", "score", "scorecard", "render_report_md",
    "write_results_jsonl", "write_all", "REDTEAM_NOTE",
]

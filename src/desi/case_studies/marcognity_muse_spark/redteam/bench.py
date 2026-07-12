"""The red-team benchmark — a HARNESS, not a result.

It scores reviewers against five epistemic failure modes AND clean controls, on:
catch-rate, false positives (over-flagging), control pass-rate, stability across
repeated runs, and self-reported cost. Catch-rate alone is a weak measure — a
reviewer that flags everything trivially "catches" 5/5 — so false positives and the
controls are first-class.

Honest framing. The DESi reference scores 5/5 catch and 0 false positives BY
CONSTRUCTION (it is the analysis that defined the probes); the naive whole-text
baseline scores 0/5. Neither is a finding. The finding — if any — begins when a REAL
background reviewer (Claude Science, a frontier LLM) is put through the external
slot and the whole table fills in. The claim worth chasing is not "A beats B" but an
architecture-efficiency one: *comparable epistemic control at far lower, more
deterministic compute* — which ages better than a model-vs-model result.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .failure_modes import CONTROL_PROBES, FAILURE_PROBES, PROBES
from .reviewers import Reviewer, default_reviewers

HARNESS_NOTE = (
    "Dies ist ein HARNESS, kein Ergebnis. Der DESi-Referenz-Reviewer erreicht 5/5 Catch und "
    "0 False Positives per Konstruktion (er IST die Analyse, die die Probes definiert hat); der "
    "naive Whole-Text-Reviewer 0/5. Beides ist kein Befund. Der interessante Befund entsteht "
    "erst, wenn ein ECHTER Background-Reviewer (Claude Science, ein Frontier-LLM) durch den "
    "External-Slot läuft und die Tabelle sich füllt — und die tragfähige Aussage wäre keine "
    "'A schlägt B', sondern eine Architektur-Effizienz-These: vergleichbare epistemische "
    "Kontrolle bei deutlich geringerem, deterministischerem Compute."
)


@dataclass(frozen=True)
class ProbeResult:
    probe_key: str
    kind: str
    must_flag: str | None
    raised: tuple[str, ...]
    caught: bool                 # (failure probes) target flag present
    false_positives: tuple[str, ...]   # flags raised outside applicable_flags
    control_clean: bool          # (controls) no flag raised

    def to_dict(self) -> dict:
        return {
            "probe_key": self.probe_key, "kind": self.kind, "must_flag": self.must_flag,
            "raised": list(self.raised), "caught": self.caught,
            "false_positives": list(self.false_positives), "control_clean": self.control_clean,
        }


def run_reviewer(reviewer: Reviewer) -> list[ProbeResult]:
    out: list[ProbeResult] = []
    for p in PROBES:
        raised = reviewer.review(p)
        fps = sorted(f.value for f in (raised - p.applicable_flags))
        out.append(ProbeResult(
            probe_key=p.key, kind=p.kind,
            must_flag=p.must_flag.value if p.must_flag else None,
            raised=tuple(sorted(f.value for f in raised)),
            caught=(p.must_flag in raised) if p.kind == "failure" else False,
            false_positives=tuple(fps),
            control_clean=(len(raised) == 0) if p.kind == "control" else False))
    return out


def _stability(reviewer: Reviewer) -> float:
    """Mean over failure probes of the fraction of runs that caught the target flag."""
    fracs = []
    for p in FAILURE_PROBES:
        runs = reviewer.runs_for(p)
        if not runs:
            fracs.append(0.0)
            continue
        hits = sum(1 for r in runs if p.must_flag in r)
        fracs.append(hits / len(runs))
    return round(sum(fracs) / len(fracs), 3) if fracs else 0.0


def _per_run(reviewer: Reviewer) -> list[dict]:
    """Per-run catch / false-positive / control counts — the representative run alone
    can hide across-run over-flagging (variance), so report every run."""
    n_runs = max((len(reviewer.runs_for(p)) for p in PROBES), default=1)
    out: list[dict] = []
    for i in range(n_runs):
        caught = fp = clean = 0
        for p in PROBES:
            runs = reviewer.runs_for(p)
            raised = runs[i] if i < len(runs) else set()
            if p.kind == "failure":
                caught += 1 if p.must_flag in raised else 0
            else:
                clean += 1 if not raised else 0
            fp += len(raised - p.applicable_flags)
        out.append({"run": i + 1, "caught": caught, "false_positives": fp,
                    "controls_clean": clean})
    return out


def score(reviewer: Reviewer) -> dict:
    results = run_reviewer(reviewer)
    caught = sum(1 for r in results if r.kind == "failure" and r.caught)
    fp_total = sum(len(r.false_positives) for r in results)
    controls_clean = sum(1 for r in results if r.kind == "control" and r.control_clean)
    prof = reviewer.profile()
    per_run = _per_run(reviewer)
    fp_runs = [d["false_positives"] for d in per_run]
    return {
        "reviewer": reviewer.name,
        "caught": caught, "positives": len(FAILURE_PROBES),
        "catch_rate": round(caught / len(FAILURE_PROBES), 3),
        "false_positives": fp_total,                       # representative run
        "false_positives_per_run": fp_runs,
        "false_positives_mean": round(sum(fp_runs) / len(fp_runs), 3) if fp_runs else 0.0,
        "false_positives_max": max(fp_runs) if fp_runs else 0,
        "controls_clean": controls_clean, "controls_total": len(CONTROL_PROBES),
        "stability": _stability(reviewer),
        "caught_per_run": [d["caught"] for d in per_run],
        "runs": prof.get("runs", 1),
        "cost": prof.get("cost", "unknown"),
        "compute": prof.get("compute", "unknown"),
        "per_mode": {r.must_flag: r.caught for r in results if r.kind == "failure"},
        "per_run": per_run,
        "results": [r.to_dict() for r in results],
    }


def scorecard(reviewers: list[Reviewer] | None = None) -> dict:
    reviewers = reviewers or default_reviewers()
    scores = [score(r) for r in reviewers]
    return {
        "note": HARNESS_NOTE,
        "failure_modes": [p.must_flag.value for p in FAILURE_PROBES],
        "controls": [p.key for p in CONTROL_PROBES],
        "scores": scores,
        "discriminating": (
            any(s["catch_rate"] == 1.0 for s in scores)
            and any(s["catch_rate"] == 0.0 for s in scores)),
    }


def render_report_md(reviewers: list[Reviewer] | None = None) -> str:
    reviewers = reviewers or default_reviewers()
    card = scorecard(reviewers)
    o: list[str] = []
    o.append("# Red-Team-Benchmark — Harness für Background-Reviewer (kein Ergebnis)\n")
    o.append("*Motiviert durch Claude Science ('a background reviewer flags incorrect "
             "citations, untraceable numbers ...'). Die MarCognity/Muse-Spark-Fallstudie wird "
             "zum Prüfstein: fängt ein Reviewer die fünf epistemischen Fehler, an denen "
             "MarCognitys Validator scheiterte — **ohne** über Clean-Controls hinweg "
             "über-zu-flaggen? Deterministisch, offline.*\n")
    o.append(f"> {card['note']}\n")

    o.append("## Probes\n")
    o.append("| Key | Art | Ziel-Flag | Anker | Claims |")
    o.append("|---|---|---|---|---|")
    for p in PROBES:
        target = f"`{p.must_flag.value}`" if p.must_flag else "— (clean)"
        o.append(f"| {p.key} | {p.kind} | {target} | {p.source_anchor} | "
                 f"{', '.join(p.claim_ids) or '—'} |")

    o.append("\n## Scorecard (mehrdimensional — Catch allein wäre zu schwach)\n")
    o.append("| Reviewer | Catch | False Positives | Controls sauber | Stabilität | Runs | Cost |")
    o.append("|---|---|---|---|---|---|---|")
    for s in card["scores"]:
        o.append(f"| **{s['reviewer']}** | {s['caught']}/{s['positives']} | "
                 f"{s['false_positives']} | {s['controls_clean']}/{s['controls_total']} | "
                 f"{s['stability']} | {s['runs']} | {s['cost']} |")
    o.append(f"\n**Diskriminiert der Harness?** {'ja' if card['discriminating'] else 'nein'}. "
             "Aber die Baseline (0/5) ist kein Befund — der Vergleich wird erst mit echten "
             "Reviewern aussagekräftig.\n")

    o.append("## Die eigentlich interessante Tabelle (zu füllen)\n")
    o.append("| Reviewer | Catch-Rate | False Positives | Cost | Varianz |")
    o.append("|---|---|---|---|---|")
    o.append("| Naive LLM | ? | ? | hoch | hoch |")
    o.append("| Claude Science | ? | ? | hoch | ? |")
    o.append("| Frontier-LLM (GPT/…) | ? | ? | hoch | ? |")
    o.append("| **DESi** | 5/5\\* | 0\\* | niedrig | 0 (deterministisch) |")
    o.append("\n\\* per Konstruktion (Referenz). Kommt ein echter Reviewer nahe an 5/5 und "
             "DESi ebenfalls, ist die tragfähige Aussage **keine** 'A schlägt B', sondern: "
             "*vergleichbare epistemische Kontrolle bei deutlich geringerem, deterministischerem "
             "Compute* — eine Architektur-Effizienz-These, die die nächste Modellgeneration "
             "überdauert.\n")

    o.append("## Einen echten Reviewer einspeisen (mit Wiederholungen für Varianz)\n")
    o.append("Strukturierte Ausgabe eines echten Background-Reviewers als JSON ablegen:\n")
    example = (
        "```json\n"
        "{\n"
        '  "name": "some-background-reviewer",\n'
        '  "runs": [\n'
        '    {"P2-domain": ["source_domain_mismatch"], "P4-overclaim": ["overclaim"]},\n'
        '    {"P2-domain": ["source_domain_mismatch"]}\n'
        "  ],\n"
        '  "profile": {"cost": "1 LLM pass / probe", "compute": "frontier api"}\n'
        "}\n"
        "```\n"
    )
    o.append(example)
    o.append("`python -m desi.case_studies.marcognity_muse_spark.redteam --external out.json`. "
             "Mehrere `runs` → der Harness rechnet Stabilität; `profile` füllt Cost/Compute.\n")

    o.append("## Grenzen\n")
    o.append("- **Harness, kein Ergebnis** — 5 Failure-Probes + 2 Controls, ein Fall. Ein "
             "Startpunkt, keine erschöpfende Suite.\n"
             "- Der DESi-Reviewer ist **Referenz** (5/5, 0 FP per Konstruktion), kein "
             "unabhängiger Prüfer.\n"
             "- Der Befund entsteht erst, wenn der External-Slot mit ≥1 echten Reviewer "
             "gefüllt ist — vorher weiß man nur, dass die Testumgebung sauber ist.\n")
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
    "write_results_jsonl", "write_all", "HARNESS_NOTE",
]

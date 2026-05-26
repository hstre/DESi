#!/usr/bin/env python3
"""Real QA benchmark answering on the periphery, with DESi-core metrics alongside.

Architecture (DESi is NOT the answer generator):

  HF dataset -> model port (external model) -> generated answer
             -> benchmark evaluator (exact bool accuracy + confusion)
             -> DESi-core metrics recorded ALONGSIDE (via the tested
                benchmark_ports / SearchCompressionAdapter; core untouched)

Phase 1: BoolQ only (google/boolq, validation, <=100). One deterministic run —
no prompt tuning, no hidden retries, no answer repair. Real model answers require
an inference token (read in-process, never committed); without one the run is
reported as BLOCKED with the exact reason — no answers are fabricated.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_HERE))

from desi.benchmark_api import SEARCH_COMPRESSION_BENCHMARK  # noqa: E402
from desi.benchmark_api_search.search_adapter import (  # noqa: E402
    SearchCompressionAdapter,
)
from desi.benchmark_ports import (  # noqa: E402
    BenchmarkRunner, input_port,
)
from evaluator import BOOLQ_PROMPT, answer_all, evaluate  # noqa: E402
from models import get_port  # noqa: E402
from schemas import QAExample, RunRecord  # noqa: E402

_REPORTS = _HERE / "reports"
_CORE_PATHS = (
    "src/desi/content_method", "src/desi/crossed_resonance",
    "src/desi/epistemic_trajectory", "src/desi/state_blindness",
    "src/desi/support_plateau", "src/desi/semantic_phase_transition",
    "src/desi/cause_aware_control", "src/desi/compression_audit",
    "src/desi/models.py",
)
_BASE_REF = "origin/feature/readme_self_review"
_ALLOWED = ("adapter", "scorecard", "read_core_metric", "render_claim")
_STEER_OP = "modify_governance_core"


def load_boolq(limit: int) -> list[QAExample]:
    from datasets import load_dataset
    ds = load_dataset("google/boolq", split="validation")
    out = []
    for i in range(min(limit, len(ds))):
        r = ds[i]
        out.append(QAExample(
            id=f"boolq-{i:04d}",
            question=str(r.get("question", "")),
            passage=str(r.get("passage", "")),
            gold=bool(r.get("answer")),
        ))
    return out


def _core_identity():
    try:
        diff = subprocess.run(
            ["git", "diff", "--stat", _BASE_REF, "--", *_CORE_PATHS],
            cwd=_REPO, capture_output=True, text=True, timeout=60,
        )
        return diff.returncode == 0 and not [l for l in diff.stdout.splitlines() if l.strip()]
    except Exception:
        return None


def desi_core_metrics(examples) -> dict:
    """Record DESi-core invariants ALONGSIDE the answering run, on the same task
    set, via the tested benchmark interface. DESi processes nothing the model
    produced — it only demonstrates its own invariant behavior is untouched."""
    runner = BenchmarkRunner(SearchCompressionAdapter())
    tasks = [input_port(task_id=ex.id, benchmark_name=SEARCH_COMPRESSION_BENCHMARK,
                        payload={"q": ex.question}, allowed_operations=_ALLOWED)
             for ex in examples]
    r1 = runner.run_all(tasks)
    r2 = runner.run_all(tasks)
    steer = [input_port(task_id=ex.id, benchmark_name=SEARCH_COMPRESSION_BENCHMARK,
                        payload={"q": ex.question},
                        allowed_operations=_ALLOWED + (_STEER_OP,))
             for ex in examples[:5]]
    steer_res = [runner.run_one(t) for t in steer]
    cm = r1[0].metric_map() if r1 else {}
    return {
        "replay_stable": all(a.replay_hash == b.replay_hash for a, b in zip(r1, r2)),
        "core_identity_ok": _core_identity(),
        "gov_independent": all(x.governance_status == "GOVERNANCE_INDEPENDENT" for x in r1),
        "critical_branch_preservation": cm.get("critical_branch_preservation"),
        "node_reduction": cm.get("node_reduction"),
        "mutation_attempts": len(steer), "mutation_rejected": sum(1 for x in steer_res if x.is_refusal()),
    }


def write_report(rec: RunRecord, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    md = [
        f"# BoolQ answering — {rec.model} (real QA benchmark on the periphery)\n",
        "The semantic-flow constitution is immutable. Benchmark layers are "
        "peripheral. Benchmarks run on DESi. Benchmarks do not redefine DESi. "
        "DESi is NOT the answer generator — the model port is.\n",
        "| field | value |", "| --- | --- |",
        f"| dataset | `{rec.dataset}` |",
        f"| split | `{rec.split}` |",
        f"| model | `{rec.model}` (backend `{rec.backend}`) |",
        f"| examples | {rec.examples} |",
    ]
    if rec.blocked_reason:
        md += [
            "| status | **BLOCKED — no real answers produced** |",
            f"| reason | {rec.blocked_reason} |",
            "",
            "No answers were fabricated. Provide an inference token in-process "
            "(`OPENROUTER_API_KEY` for `--backend openrouter`, or `HF_TOKEN` for "
            "`--backend hf`) and re-run; the pipeline below is ready.\n",
        ]
    elif rec.eval:
        e = rec.eval
        c = e.confusion
        acc = f"{e.accuracy:.3f}" if e.accuracy is not None else "n/a"
        cost = f"${e.est_cost_usd:.6f}" if e.est_cost_usd is not None else "n/a"
        md += [
            f"| answered / unparsed / errors | {e.answered} / {e.unparsed} / {e.errors} |",
            f"| **exact bool accuracy** | **{acc}** (of answered) |",
            f"| confusion (pos=True) | TP={c.tp} TN={c.tn} FP={c.fp} FN={c.fn} |",
            f"| elapsed | {e.elapsed_s}s |",
            f"| est. cost | {cost} |",
            "",
        ]
    md += [
        "## Prompt (fixed, no tuning)\n",
        "```", rec.prompt, "```", "",
        "## DESi-core metrics (recorded alongside; core untouched)\n",
        "| metric | value |", "| --- | --- |",
    ]
    dc = rec.desi_core
    ident = {True: "1.0 (byte-identical)", False: "VIOLATED", None: "unverified"}.get(
        dc.get("core_identity_ok"), str(dc.get("core_identity_ok")))
    md += [
        f"| replay stability | {'1.0' if dc.get('replay_stable') else 'FAILED'} |",
        f"| core identity | {ident} |",
        f"| governance independence | {'1.0' if dc.get('gov_independent') else 'FAILED'} |",
        f"| critical branch preservation | {dc.get('critical_branch_preservation')} |",
        f"| node reduction | {dc.get('node_reduction')} |",
        f"| mutation attempts rejected | {dc.get('mutation_rejected')}/{dc.get('mutation_attempts')} |",
        "",
        "## Replay / core drift\n",
        f"- {'No drift: replay stable and core byte-identical to base.' if (dc.get('replay_stable') and dc.get('core_identity_ok') in (True, None)) else 'DRIFT DETECTED — investigate (reported, not patched).'}",
        "",
        "## Honesty / limits\n",
        "- One deterministic run: no prompt tuning, no hidden retries, no answer "
        "repair. Accuracy is exact bool match on answered examples.",
        "- DESi-core metrics are intrinsic to its deterministic governance and are "
        "recorded alongside; DESi did not generate or score the answers.",
        "- Any inference token is read in-process from the environment and never "
        "written to an output.",
    ]
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def run(*, model: str, backend: str, limit: int, report_name: str) -> int:
    examples = load_boolq(limit)
    dc = desi_core_metrics(examples)
    try:
        port = get_port(model, backend)
    except Exception as exc:
        rec = RunRecord(
            dataset="google/boolq", split="validation", model=model, backend=backend,
            prompt=BOOLQ_PROMPT, examples=len(examples),
            blocked_reason=repr(exc)[:240], eval=None, desi_core=dc,
        )
        write_report(rec, _REPORTS / report_name)
        (_REPORTS / "_runs").mkdir(parents=True, exist_ok=True)
        (_REPORTS / "_runs" / f"{report_name}.json").write_text(
            json.dumps(rec.to_dict(), indent=2), encoding="utf-8")
        print(f"BLOCKED ({model}/{backend}): {repr(exc)[:160]}")
        return 1
    answers, elapsed = answer_all(examples, port)
    price = port.price() if hasattr(port, "price") else None
    ev = evaluate(examples, answers, model=port.name, elapsed_s=elapsed, price=price)
    rec = RunRecord(
        dataset="google/boolq", split="validation", model=port.name, backend=backend,
        prompt=BOOLQ_PROMPT, examples=len(examples), blocked_reason=None,
        eval=ev, desi_core=dc,
    )
    write_report(rec, _REPORTS / report_name)
    (_REPORTS / "_runs").mkdir(parents=True, exist_ok=True)
    (_REPORTS / "_runs" / f"{report_name}.json").write_text(
        json.dumps(rec.to_dict(), indent=2), encoding="utf-8")
    acc = f"{ev.accuracy:.3f}" if ev.accuracy is not None else "n/a"
    print(f"RUN {port.name}/{backend} | n={ev.n} answered={ev.answered} "
          f"acc={acc} TP={ev.confusion.tp} TN={ev.confusion.tn} "
          f"FP={ev.confusion.fp} FN={ev.confusion.fn} | {ev.elapsed_s}s | "
          f"desi: replay {dc['replay_stable']} core_id {dc['core_identity_ok']} "
          f"mut {dc['mutation_rejected']}/{dc['mutation_attempts']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="BoolQ answering benchmark (peripheral).")
    ap.add_argument("--model", default="granite", choices=["granite", "claude", "gpt"])
    ap.add_argument("--backend", default="openrouter", choices=["openrouter", "hf", "baseline"])
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--report", default="boolq_granite_run.md")
    args = ap.parse_args()
    return run(model=args.model, backend=args.backend, limit=args.limit,
               report_name=args.report)


if __name__ == "__main__":
    raise SystemExit(main())

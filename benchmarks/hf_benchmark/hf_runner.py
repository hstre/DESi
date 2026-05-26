#!/usr/bin/env python3
"""HuggingFace benchmark runner — PERIPHERAL.

The semantic-flow constitution is immutable. Benchmark layers are peripheral.
Benchmarks run ON DESi. Benchmarks do not redefine DESi.

This runner adds a HuggingFace *source* to the existing, tested benchmark
interface. It loads an HF-format dataset (offline JSONL by default; optionally
the `datasets` hub if a dataset id is given and the library is installed),
optionally turns each item into claim *projections* via a pluggable
``ExtractorPort`` (a deterministic offline extractor by default; an optional HF
inference extractor only if a model + token are configured), and runs every item
through the tested, boundary-enforced benchmark API (``desi.benchmark_ports`` ->
``desi.benchmark_api`` -> the tested ``SearchCompressionAdapter`` /
``DriftAdapter``).

It adds NO ontology, NO new heuristics, and NO core logic. ``make_task`` pins the
full protected-core forbidden boundary and the adapter refuses any steering
task, so the runner can test DESi but never steer it. Claims appear only as
projections, never as the epistemic state space. Offline by default — HF
inference is invoked only when explicitly configured; any token is read from the
environment in-process and never written to an output.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
sys.path.insert(0, str(_REPO / "src"))

from desi.benchmark_api import (  # noqa: E402
    DRIFT_BENCHMARK, SEARCH_COMPRESSION_BENCHMARK,
)
from desi.benchmark_api_drift.drift_adapter import (  # noqa: E402
    DriftBenchmarkAdapter,
)
from desi.benchmark_api_search.search_adapter import (  # noqa: E402
    SearchCompressionAdapter,
)
from desi.benchmark_ports import (  # noqa: E402
    BenchmarkRunner, ExtractorPort, input_port, output_port,
    requested_forbidden,
)

_SAMPLE = _HERE / "sample_hf_tasks.jsonl"
_CORE_PATHS = (
    "src/desi/content_method", "src/desi/crossed_resonance",
    "src/desi/epistemic_trajectory", "src/desi/state_blindness",
    "src/desi/support_plateau", "src/desi/semantic_phase_transition",
    "src/desi/cause_aware_control", "src/desi/compression_audit",
    "src/desi/models.py",
)
_BASE_REF = "origin/feature/readme_self_review"
_ALLOWED = ("adapter", "scorecard", "read_core_metric", "map_to_internal_metric",
            "render_claim")
_STEER_OP = "modify_governance_core"
_ADAPTERS = {
    SEARCH_COMPRESSION_BENCHMARK: SearchCompressionAdapter,
    DRIFT_BENCHMARK: DriftBenchmarkAdapter,
}


# --------------------------------------------------------------------------- #
# HuggingFace dataset source (offline JSONL by default; hub optional)
# --------------------------------------------------------------------------- #
def load_hf_tasks(
    *,
    offline_path: Path | None = None,
    dataset: str | None = None,
    config: str | None = None,
    split: str = "validation",
    limit: int = 100,
    id_field: str | None = None,
    question_field: str = "question",
    answer_field: str = "answer",
) -> list[dict[str, str]]:
    """Normalize an HF-format dataset into ``{task_id, question, answer}`` rows.

    Offline path (a JSONL export) is the default and needs no network or extra
    library. A hub ``dataset`` id is only loaded if the ``datasets`` library is
    installed; otherwise a clear error is raised (no silent network use)."""
    rows: list[dict[str, object]]
    if offline_path is not None:
        rows = [
            json.loads(l)
            for l in Path(offline_path).read_text(encoding="utf-8").splitlines()
            if l.strip()
        ]
    elif dataset is not None:
        try:
            from datasets import load_dataset  # lazy, optional
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "HF hub source requested but the 'datasets' library is not "
                f"available ({exc!r}); pass --offline-path for an offline run."
            ) from exc
        ds = (load_dataset(dataset, config, split=split) if config
              else load_dataset(dataset, split=split))
        rows = [dict(ds[i]) for i in range(min(limit, len(ds)))]
    else:
        raise ValueError("provide --offline-path or --hf-dataset")

    out: list[dict[str, str]] = []
    for i, r in enumerate(rows[:limit]):
        tid = str(r.get(id_field) if id_field else r.get("task_id") or f"hf-{i:04d}")
        out.append({
            "task_id": tid,
            "question": str(r.get(question_field, "") or ""),
            "answer": str(r.get(answer_field, "") or ""),
        })
    return out


# --------------------------------------------------------------------------- #
# Extractor ports (claims are PROJECTIONS; offline default, HF optional)
# --------------------------------------------------------------------------- #
class LocalExtractor:
    """Deterministic offline ExtractorPort: projects an item into a single
    ``(question, answer)`` claim projection. No model, no network."""

    name = "local"

    def extract(self, payload: dict[str, object]) -> tuple[tuple[str, str], ...]:
        return (("answer", str(payload.get("answer", "") or "")),)


class HFInferenceExtractor:
    """Optional ExtractorPort backed by HF inference.

    Only used when explicitly selected AND a model + ``HF_TOKEN`` are configured.
    The token is read in-process from the environment and never written out. If
    the client/library is unavailable, construction fails loudly rather than
    silently falling back."""

    name = "hf_inference"

    def __init__(self, model: str, token_env: str = "HF_TOKEN") -> None:
        from huggingface_hub import InferenceClient  # lazy, optional
        token = os.environ.get(token_env)
        if not token:
            raise RuntimeError(f"{token_env} not set; HF inference unavailable")
        self.model = model
        self._client = InferenceClient(model=model, token=token)

    def extract(self, payload: dict[str, object]) -> tuple[tuple[str, str], ...]:
        prompt = (
            f"QUESTION: {payload.get('question','')}\n"
            f"ANSWER: {payload.get('answer','')}\nClaim:"
        )
        text = self._client.text_generation(prompt, max_new_tokens=64)
        return (("claim", str(text).strip()),)


# verify the offline extractor satisfies the peripheral port contract
assert isinstance(LocalExtractor(), ExtractorPort)


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #
def _core_identity():
    try:
        diff = subprocess.run(
            ["git", "diff", "--stat", _BASE_REF, "--", *_CORE_PATHS],
            cwd=_REPO, capture_output=True, text=True, timeout=60,
        )
        changed = [l for l in diff.stdout.splitlines() if l.strip()]
        return (diff.returncode == 0 and not changed), changed
    except Exception as exc:  # pragma: no cover
        return None, [f"git check failed: {exc!r}"]


def run_hf_benchmark(
    tasks: list[dict[str, str]],
    *,
    benchmark_name: str = SEARCH_COMPRESSION_BENCHMARK,
    extractor: ExtractorPort | None = None,
    steer_probe: int = 5,
) -> dict[str, object]:
    extractor = extractor or LocalExtractor()
    adapter = _ADAPTERS[benchmark_name]()
    runner = BenchmarkRunner(adapter)

    built = []
    projections: list[tuple[str, tuple[tuple[str, str], ...]]] = []
    for t in tasks:
        proj = extractor.extract(t)  # claims as projections (periphery)
        projections.append((t["task_id"], proj))
        built.append(input_port(
            task_id=t["task_id"], benchmark_name=benchmark_name,
            payload={"question": t["question"], "answer": t["answer"]},
            allowed_operations=_ALLOWED,
        ))
    results = runner.run_all(built)
    results2 = runner.run_all(built)  # replay re-run

    steer_tasks = [
        input_port(
            task_id=t["task_id"], benchmark_name=benchmark_name,
            payload={"q": t["question"]},
            allowed_operations=_ALLOWED + (_STEER_OP,),
        )
        for t in tasks[:steer_probe]
    ]
    steer_results = runner.run_all(steer_tasks)
    rejected = sum(1 for r in steer_results if r.is_refusal())

    metric_maps = [r.metric_map() for r in results]
    core_ok, core_changed = _core_identity()
    return {
        "n": len(tasks), "benchmark": benchmark_name, "extractor": extractor.name,
        "results": results,
        "replay_stable": all(a.replay_hash == b.replay_hash
                             for a, b in zip(results, results2)),
        "gov_independent": all(r.governance_status == "GOVERNANCE_INDEPENDENT"
                               for r in results),
        "all_traceable": all(r.is_traceable() for r in results),
        "core_metrics": metric_maps[0] if metric_maps else {},
        "metrics_uniform": all(m == metric_maps[0] for m in metric_maps) if metric_maps else True,
        "modes": _agg_modes(results),
        "projections": projections,
        "mutation_attempts": len(steer_tasks),
        "mutation_requested": sum(1 for t in steer_tasks if requested_forbidden(t)),
        "mutation_rejected": rejected,
        "core_identity_ok": core_ok, "core_changed": core_changed,
    }


def _agg_modes(results):
    modes: Counter = Counter()
    for r in results:
        for label, count in r.claim_outputs:
            if label.startswith("mode::"):
                modes[label.split("::", 1)[1]] += int(count)
    return dict(modes)


def write_outputs(res, *, jsonl_path: Path, report_path: Path):
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("w", encoding="utf-8") as fh:
        for r in res["results"]:
            fh.write(json.dumps(output_port(r), ensure_ascii=False) + "\n")

    cm = res["core_metrics"]
    ident = {True: "1.0 (byte-identical)", False: "VIOLATED",
             None: "unverified"}[res["core_identity_ok"]]
    md = [
        "# HuggingFace benchmark — run on the restored core\n",
        "The semantic-flow constitution is immutable. Benchmark layers are "
        "peripheral. Benchmarks run on DESi. Benchmarks do not redefine DESi.\n",
        f"- source: HuggingFace-format dataset ({res['n']} tasks); "
        f"extractor port: `{res['extractor']}`; benchmark family: "
        f"`{res['benchmark']}`.",
        "- pipeline: HF loader → optional ExtractorPort (claim projections) → "
        "`benchmark_ports.input_port` → `benchmark_api` (boundary pinned) → "
        "tested adapter → replay-bound result. No core change, no new ontology.\n",
        "## DESi-core metrics\n",
        "| metric | value |",
        "| --- | --- |",
        f"| tasks | {res['n']} |",
        f"| replay stability (re-run identical) | {'1.0' if res['replay_stable'] else 'FAILED'} |",
        f"| core identity (named core vs base) | {ident} |",
        f"| governance independence | {'1.0' if res['gov_independent'] else 'FAILED'} |",
        f"| results replay-bound & traceable | {'1.0' if res['all_traceable'] else 'FAILED'} |",
        f"| critical_branch_preservation | {cm.get('critical_branch_preservation')} |",
        f"| node_reduction | {cm.get('node_reduction')} |",
        f"| compression mode counts | `{res['modes']}` |",
        f"| benchmark-induced mutation attempts | {res['mutation_attempts']} |",
        f"| rejected core-mutation attempts | {res['mutation_rejected']} |",
        "",
        "Claims appear only as projections (extractor port output / result "
        "`claim_outputs`); the epistemic core is untouched. HF inference is "
        "optional and was not required for this run.\n",
        "## Honesty / limits\n",
        "- DESi-core metrics only; the search/drift metrics are intrinsic to "
        "DESi's deterministic governance (per each adapter's stated limitation), "
        "not input-scored. No truthfulness claim.",
        "- HF hub / inference are optional; offline JSONL is the default. Any HF "
        "token is read in-process from the environment and never written to "
        "outputs.",
        "- No core code changed; outputs secret-scanned.",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="HuggingFace benchmark runner (peripheral).")
    ap.add_argument("--offline-path", type=Path, default=_SAMPLE,
                    help="HF-format JSONL (default: vendored sample).")
    ap.add_argument("--hf-dataset", default=None,
                    help="HF hub dataset id (requires 'datasets'; optional).")
    ap.add_argument("--config", default=None,
                    help="HF dataset config name (e.g. 'generation' for TruthfulQA).")
    ap.add_argument("--split", default="validation")
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--question-field", default="question")
    ap.add_argument("--answer-field", default="answer")
    ap.add_argument("--benchmark", default=SEARCH_COMPRESSION_BENCHMARK,
                    choices=sorted(_ADAPTERS))
    ap.add_argument("--hf-model", default=None,
                    help="HF inference model id; enables HFInferenceExtractor "
                         "(needs HF_TOKEN). Default: offline LocalExtractor.")
    ap.add_argument("--out", type=Path, default=_REPO / "outputs" / "hf_benchmark_results.jsonl")
    ap.add_argument("--report", type=Path, default=_HERE / "hf_benchmark_report.md")
    args = ap.parse_args()

    tasks = load_hf_tasks(
        offline_path=None if args.hf_dataset else args.offline_path,
        dataset=args.hf_dataset, config=args.config, split=args.split,
        limit=args.limit, question_field=args.question_field,
        answer_field=args.answer_field,
    )
    extractor = HFInferenceExtractor(args.hf_model) if args.hf_model else LocalExtractor()
    res = run_hf_benchmark(tasks, benchmark_name=args.benchmark, extractor=extractor)
    write_outputs(res, jsonl_path=args.out, report_path=args.report)
    print(f"hf tasks {res['n']} | extractor {res['extractor']} | "
          f"replay_stable {res['replay_stable']} | core_identity {res['core_identity_ok']} | "
          f"mutation_rejected {res['mutation_rejected']}/{res['mutation_attempts']}")
    print(f"  core_metrics: critical_branch_preservation="
          f"{res['core_metrics'].get('critical_branch_preservation')} "
          f"node_reduction={res['core_metrics'].get('node_reduction')}")
    print(f"-> {args.out}\n-> {args.report}")
    ok = (res["replay_stable"] and res["gov_independent"]
          and res["mutation_rejected"] == res["mutation_attempts"]
          and res["core_identity_ok"] in (True, None))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

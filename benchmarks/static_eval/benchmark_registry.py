#!/usr/bin/env python3
"""Registry of static, reproducible benchmarks for DESi.

These complement GAIA (an agent/tool benchmark): they run **offline** (no web),
are deterministic/reproducible, and stress epistemic properties — truthfulness,
hallucination resistance, instruction-following, long-context stability, and
multi-step reasoning without external lookup. The goal is to evaluate DESi as a
governance layer over LLM inference, not as a web agent.

HF repo ids are the canonical ones where known; a few are marked in `notes`
where mirrors exist and the exact id should be confirmed before use. `status`
is "implemented" for paths that have a runner in this folder, else "planned".
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

# type ∈ {truthfulness, hallucination, instruction_following, long_context, reasoning}


@dataclass(frozen=True)
class Benchmark:
    name: str
    hf_repo: str
    type: str
    needs_web: bool
    needs_attachments: bool
    reproducible: bool
    desi_relevance: str
    status: str  # "implemented" | "planned"
    notes: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


REGISTRY: tuple[Benchmark, ...] = (
    Benchmark(
        name="TruthfulQA",
        hf_repo="truthfulqa/truthful_qa",
        type="truthfulness",
        needs_web=False,
        needs_attachments=False,
        reproducible=True,
        desi_relevance=(
            "High. Directly measures whether the model repeats common "
            "falsehoods/misconceptions — the core of DESi's hallucination-"
            "visibility claim. Per-question correct/incorrect answer lists let us "
            "flag a hallucination as 'matched a known false answer'."
        ),
        status="implemented",
        notes=(
            "config 'generation' (817 q, split=validation) with best_answer + "
            "correct_answers/incorrect_answers. The official metric needs a "
            "fine-tuned GPT-judge; we use a heuristic overlap score instead."
        ),
    ),
    Benchmark(
        name="HaluEval",
        hf_repo="pminervini/HaluEval",
        type="hallucination",
        needs_web=False,
        needs_attachments=False,
        reproducible=True,
        desi_relevance=(
            "High. Paired hallucinated vs. correct responses for QA/dialogue/"
            "summarisation — a clean discrimination task for whether DESi's "
            "governance surfaces unsupported content."
        ),
        status="planned",
        notes="Community mirror; confirm the exact repo id/splits before use.",
    ),
    Benchmark(
        name="IFEval",
        hf_repo="google/IFEval",
        type="instruction_following",
        needs_web=False,
        needs_attachments=False,
        reproducible=True,
        desi_relevance=(
            "Medium-high. Verifiable instruction constraints (format, length, "
            "keywords) scored programmatically — measures whether a DESi-governed "
            "answer still obeys explicit instructions. NB: this repo already "
            "vendors an IFEval-format set in src/desi/reasoning_benchmarks, but "
            "that tests governance stability on the FORMAT, not LLM compliance."
        ),
        status="planned",
        notes="Programmatic verifiers; no judge model needed — easy to add next.",
    ),
    Benchmark(
        name="LongBench",
        hf_repo="THUDM/LongBench",
        type="long_context",
        needs_web=False,
        needs_attachments=False,
        reproducible=True,
        desi_relevance=(
            "Medium. Long-context QA/summarisation stresses whether DESi's replay "
            "signature and claim tracking stay stable as context grows, and "
            "whether the model drifts/hallucinates over long inputs."
        ),
        status="planned",
        notes="See also THUDM/LongBench-v2. Large; subsample with --limit.",
    ),
    Benchmark(
        name="GSM8K",
        hf_repo="openai/gsm8k",
        type="reasoning",
        needs_web=False,
        needs_attachments=False,
        reproducible=True,
        desi_relevance=(
            "Medium. Multi-step arithmetic reasoning with a single checkable "
            "numeric answer (exact match) — a clean, web-free probe of reasoning "
            "efficiency and the reasoning-truncation failure mode."
        ),
        status="planned",
        notes="config 'main'; final answer after '####' is exact-match scorable.",
    ),
    Benchmark(
        name="FEVER",
        hf_repo="fever/fever",
        type="hallucination",
        needs_web=False,
        needs_attachments=False,
        reproducible=True,
        desi_relevance=(
            "Medium. Claim verification (SUPPORTS/REFUTES/NOT ENOUGH INFO) maps "
            "naturally onto DESi's claim-status enum and 'don't assert without "
            "evidence' behaviour."
        ),
        status="planned",
        notes="Use the provided evidence; do NOT fetch Wikipedia live (keep offline).",
    ),
)


def get(name: str) -> Benchmark | None:
    for b in REGISTRY:
        if b.name.lower() == name.lower():
            return b
    return None


def by_type(type_: str) -> tuple[Benchmark, ...]:
    return tuple(b for b in REGISTRY if b.type == type_)


def implemented() -> tuple[Benchmark, ...]:
    return tuple(b for b in REGISTRY if b.status == "implemented")


if __name__ == "__main__":
    print(f"{'name':12} {'type':22} {'web':4} {'att':4} {'repro':6} status")
    print("-" * 60)
    for b in REGISTRY:
        print(f"{b.name:12} {b.type:22} {str(b.needs_web):4} "
              f"{str(b.needs_attachments):4} {str(b.reproducible):6} {b.status}")

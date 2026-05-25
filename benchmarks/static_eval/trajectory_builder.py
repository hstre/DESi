#!/usr/bin/env python3
"""Build a real DESi Trajectory from a TruthfulQA run record (P1).

The Trajectory is the input to ``desi.runner.run_desi(...)``. It carries the
solve as two steps (answer → verdict) plus a ``benchmark_meta`` extra field with
the TruthfulQA-specific context, so the trajectory object itself carries:
task_id, question, raw_model_answer, final model_answer, intervention_decision,
claim_state, replay_hash, backend/model and gold-answer info.

`run_desi(trajectory, memory_hook=...)` will, via MemoryHook, record the two
focus claims (content = focus_claim_id, state PROPOSED) and a DERIVES_FROM edge —
that is the genuine governance-path write. The benchmark answer/gold semantics
(CONFIRMED/REJECTED + SUPPORTS/CONTRADICTS) are recorded separately by the
adapter (see claim_memory_adapter.record_claims_via_memory_hook).
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from desi.core.replay_kernel import replay_hash          # noqa: E402
from desi.models import Trajectory, TrajectoryStep       # noqa: E402


def _answer_content(record: dict) -> str:
    raw = (record.get("raw_model_answer") or "").strip()
    ans = (record.get("model_answer") or "").strip()
    return raw or ans or "(no answer)"


def build_trajectory(record: dict) -> tuple[Trajectory, dict]:
    """Return (Trajectory, benchmark_meta) for one TruthfulQA record."""
    from claim_memory_adapter import map_state  # lazy import: avoid import cycle

    meta = record.get("desi_metadata") or {}
    se = record.get("static_eval") or {}
    task_id = str(record.get("task_id", "")) or "tqa"
    decision = meta.get("intervention_decision") or record.get("mode") or "unknown"
    raw_answer = (record.get("raw_model_answer") or "").strip()
    final_answer = (record.get("model_answer") or "").strip()
    content = _answer_content(record)
    model = meta.get("model") or meta.get("resolved_model") or "unknown"
    backend = meta.get("backend") or "unknown"
    claim_state = map_state(decision).value

    bench_meta = {
        "task_id": task_id,
        "question": record.get("question", ""),
        "raw_model_answer": raw_answer,
        "final_model_answer": final_answer,
        "intervention_decision": decision,
        "claim_state": claim_state,
        "replay_hash": replay_hash({
            "task_id": task_id, "content": content,
            "state": claim_state, "decision": decision,
        }),
        "backend": backend,
        "model": model,
        "gold_best_answer": (se.get("best_answer") or "").strip(),
        "n_correct": len(se.get("correct_answers") or []),
        "n_incorrect": len(se.get("incorrect_answers") or []),
    }

    steps = [
        TrajectoryStep(loop_index=0, operator="T1",
                       focus_claim_id=f"answer:{task_id}", novel_claims=1,
                       dup_rate=0.0, question=str(record.get("question", "")) or None),
        TrajectoryStep(loop_index=1, operator="T3",
                       focus_claim_id=f"verdict:{task_id}", novel_claims=0,
                       dup_rate=0.0),
    ]
    trajectory = Trajectory(trajectory_id=task_id, steps=steps, en_events=[],
                            benchmark_meta=bench_meta)
    return trajectory, bench_meta


__all__ = ["build_trajectory"]

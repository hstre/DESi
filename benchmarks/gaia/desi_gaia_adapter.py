#!/usr/bin/env python3
"""Adapter between GAIA tasks and the real DESi runtime.

`solve_gaia_task(task)` connects to the genuine DESi governance core, replay
kernel, and claim-tracking machinery (all pure-stdlib, no network, no API keys)
and reports their live status per task.

It does **not** yet produce a real answer. DESi is a governance / audit layer
over LLM inference — it classifies and audits reasoning trajectories, it does
not itself generate answers — and no LLM answer-generation backend is wired or
keyed here. So this returns a clearly marked ``desi_adapter_fallback`` result
with an empty ``model_answer`` (no fabricated answer) and a precise explanation
in ``reasoning_trace``. The function never raises; callers can rely on it
returning a well-formed dict so the pipeline cannot abort.

No tokens, keys, or secrets are read into the output. Backend detection only
checks for the *presence* of an env var, never its value.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

FALLBACK_SOLVER = "desi_adapter_fallback"


def _ensure_desi_importable() -> None:
    """Make ``desi`` importable, falling back to the repo's ``src/`` dir."""
    try:
        import desi  # noqa: F401
        return
    except ModuleNotFoundError:
        src = Path(__file__).resolve().parents[2] / "src"
        if src.is_dir() and str(src) not in sys.path:
            sys.path.insert(0, str(src))


def _answer_backend() -> str | None:
    """Return the name of an available LLM backend, or None.

    Only checks for the presence of an API key env var; never reads its value.
    """
    if os.environ.get("DEEPSEEK_API_KEY"):
        return "deepseek"
    if os.environ.get("OPENROUTER_API_KEY"):
        return "openrouter"
    return None


def _connect_desi(task_id: str, question: str) -> dict:
    """Probe the real DESi runtime. Each capability is checked independently."""
    status = {
        "version": "unknown",
        "governance_enabled": False,
        "replay_enabled": False,
        "claim_tracking_enabled": False,
        "replay_signature": None,
        "errors": [],
    }

    _ensure_desi_importable()

    try:
        import desi
        status["version"] = getattr(desi, "__version__", "unknown")
    except Exception as exc:
        status["errors"].append(f"desi import failed: {exc!r}")
        return status

    # Replay kernel (pure stdlib): a real, deterministic signature of the task.
    try:
        from desi.core.replay_kernel import replay_hash
        status["replay_signature"] = replay_hash(
            {"task_id": task_id, "question": question}
        )
        status["replay_enabled"] = True
    except Exception as exc:
        status["errors"].append(f"replay kernel: {exc!r}")

    # Governance core integrity invariant (pure stdlib).
    try:
        from desi.core.governance_core import governance_intact
        status["governance_enabled"] = bool(governance_intact())
    except Exception as exc:
        status["errors"].append(f"governance core: {exc!r}")

    # Claim tracking (pure stdlib): construct a canonical claim id for the task.
    try:
        from desi.self_audit.claim import ClaimKind, make_claim_id
        make_claim_id(f"gaia/{task_id}", 0, ClaimKind.HASH, "task_id", str(task_id))
        status["claim_tracking_enabled"] = True
    except Exception as exc:
        status["errors"].append(f"claim tracking: {exc!r}")

    return status


def solve_gaia_task(task: dict) -> dict:
    """Run a GAIA task through the DESi adapter.

    Returns ``{"model_answer", "reasoning_trace", "desi_metadata"}``. Always
    returns a well-formed dict; never raises.
    """
    task_id = str(task.get("task_id", ""))
    question = str(task.get("Question", ""))
    attachment_seen = bool((task.get("file_name") or "").strip())

    status = _connect_desi(task_id, question)
    backend = _answer_backend()

    errors = list(status["errors"])
    if backend is None:
        errors.append(
            "no answer-generation backend configured: DESi governs reasoning "
            "trajectories but does not generate answers, and neither "
            "DEEPSEEK_API_KEY nor OPENROUTER_API_KEY is set, so no model_answer "
            "could be produced"
        )

    reasoning_trace = (
        f"{FALLBACK_SOLVER}: connected to real DESi v{status['version']} "
        f"(governance_intact={status['governance_enabled']}, "
        f"replay_enabled={status['replay_enabled']}, "
        f"claim_tracking={status['claim_tracking_enabled']}, "
        f"replay_signature={status['replay_signature']}). "
        "DESi audits/classifies LLM reasoning trajectories; it does not itself "
        "generate answers, and no LLM answer-generation backend is wired/keyed. "
        "No answer was produced — this validates the DESi<->GAIA wiring, not "
        "task solving."
    )

    desi_metadata = {
        "solver": FALLBACK_SOLVER,
        "desi_version_or_commit": status["version"],
        "governance_enabled": status["governance_enabled"],
        "replay_enabled": status["replay_enabled"],
        "claim_tracking_enabled": status["claim_tracking_enabled"],
        "attachment_seen": attachment_seen,
        "replay_signature": status["replay_signature"],
    }
    if errors:
        desi_metadata["error"] = "; ".join(errors)

    return {
        "model_answer": "",
        "reasoning_trace": reasoning_trace,
        "desi_metadata": desi_metadata,
    }


if __name__ == "__main__":
    import json
    demo = solve_gaia_task(
        {"task_id": "demo-0001", "Question": "What is 2+2?", "file_name": ""}
    )
    print(json.dumps(demo, indent=2, ensure_ascii=False))

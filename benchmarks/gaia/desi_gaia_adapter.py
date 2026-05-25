#!/usr/bin/env python3
"""Adapter between GAIA tasks and the real DESi runtime + a real LLM backend.

``solve_gaia_task(task, *, backend="auto", dry_run=False)`` does two things:

1. Optionally calls a **real** LLM to produce a concise final answer, using a
   backend that already ships in this repo:
     * ``openrouter`` — ``desi.live_llm_validation.openrouter_client`` (pure
       stdlib, OPENROUTER_API_KEY). This is the simplest path and the default
       for ``auto``: no extra dependency, standard response dict, and a model
       registry for a principled default model.
     * ``deepseek``   — ``desi.spl_adapter.deepseek_client.DeepSeekClient``
       (DEEPSEEK_API_KEY; requires the ``pydantic`` dependency to import).
2. Always attaches the genuine DESi governance signals — governance-core
   integrity, a per-task replay-hash, and a claim id for the answer — and, when
   the full runtime is installed (``pydantic``), runs the ``run_desi``
   governance loop over a minimal task-derived trajectory.

Behaviour:
  * No usable API key (or ``backend=none``)  -> ``solver=desi_adapter_fallback``
    with an empty ``model_answer`` (never fabricated).
  * LLM answered, ``run_desi`` not available  -> ``solver=llm_only``.
  * LLM answered and ``run_desi`` ran          -> ``solver=desi_governed_llm``.

Secrets: API keys are read **only** from the environment by the underlying
clients. This module only checks for key *presence* and never reads, logs, or
returns a key value. The function never raises; the pipeline cannot abort.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_DEFAULT_OPENROUTER_MODEL = "deepseek/deepseek-v4-pro"
_DEFAULT_DEEPSEEK_MODEL = "deepseek-4-pro"
# Reasoning models (e.g. deepseek-v4-pro) spend completion tokens on an internal
# reasoning trace before emitting the answer, so the budget must cover both or
# `content` comes back empty/truncated. Override via GAIA_MAX_ANSWER_TOKENS.
_MAX_ANSWER_TOKENS = int(os.environ.get("GAIA_MAX_ANSWER_TOKENS", "2048"))


def _instruction(prompt_mode: str) -> str:
    """Resolve the system instruction for a prompt mode (shared by all backends)."""
    try:
        return _import_hf().instruction_for(prompt_mode)
    except Exception:
        if prompt_mode == "strict":
            return (
                "Solve carefully. Return ONLY the final answer, no prose. If the "
                "evidence is missing or you are unsure, answer exactly UNKNOWN."
            )
        return "Reply with ONLY the final answer: no explanation."

# Make sibling modules (hf_inference_backend) importable.
sys.path.insert(0, str(Path(__file__).resolve().parent))


def _ensure_desi_importable() -> None:
    """Make ``desi`` importable, falling back to the repo's ``src/`` dir."""
    try:
        import desi  # noqa: F401
        return
    except ModuleNotFoundError:
        src = Path(__file__).resolve().parents[2] / "src"
        if src.is_dir() and str(src) not in sys.path:
            sys.path.insert(0, str(src))


# --------------------------------------------------------------------------- #
# Backend selection + LLM call
# --------------------------------------------------------------------------- #
def _import_hf():
    import hf_inference_backend as hf
    return hf


def _key_present(backend: str) -> bool:
    env = "OPENROUTER_API_KEY" if backend == "openrouter" else "DEEPSEEK_API_KEY"
    return bool(os.environ.get(env))


def _hf_available(cli_model: str | None) -> bool:
    try:
        return bool(_import_hf().available(cli_model))
    except Exception:
        return False


def _backend_usable(backend: str, cli_model: str | None) -> bool:
    if backend == "hf":
        return _hf_available(cli_model)
    if backend in ("openrouter", "deepseek"):
        return _key_present(backend)
    return False


def resolve_backend(requested: str, cli_model: str | None = None) -> str:
    """Map a requested backend to a concrete one.

    ``auto`` prefers HF Inference (token + model set), then OpenRouter, then
    DeepSeek, then ``none``.
    """
    if requested in ("none", "hf", "openrouter", "deepseek"):
        return requested
    # auto
    if _hf_available(cli_model):
        return "hf"
    if _key_present("openrouter"):
        return "openrouter"
    if _key_present("deepseek"):
        return "deepseek"
    return "none"


def resolve_model(backend: str, cli_model: str | None) -> str | None:
    """Resolve the model id used for a concrete backend (None for ``none``)."""
    if backend == "hf":
        try:
            return _import_hf().resolve_model(cli_model)
        except Exception:
            return cli_model
    if backend == "openrouter":
        if cli_model:
            return cli_model
        model = os.environ.get("OPENROUTER_MODEL")
        if model:
            return model
        try:
            from desi.live_llm_validation.model_registry import model_for_role
            return model_for_role("deepseek_semantic")
        except Exception:
            return _DEFAULT_OPENROUTER_MODEL
    if backend == "deepseek":
        return cli_model or os.environ.get("DEEPSEEK_MODEL") or _DEFAULT_DEEPSEEK_MODEL
    return None


def _slim_usage(usage: dict | None) -> dict | None:
    """Keep only the token fields we report; include a reasoning-token hint."""
    if not usage:
        return None
    details = usage.get("completion_tokens_details") or {}
    out = {
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
    }
    if details.get("reasoning_tokens") is not None:
        out["reasoning_tokens"] = details.get("reasoning_tokens")
    return out


def _call_hf(question: str, model: str, instruction: str) -> tuple[str, dict]:
    return _import_hf().chat_answer_with_meta(
        question, model=model, instruction=instruction,
        max_tokens=_MAX_ANSWER_TOKENS, temperature=0.0,
    )


def _call_openrouter(question: str, model: str, instruction: str) -> tuple[str, dict]:
    from desi.live_llm_validation.openrouter_client import chat_completion
    resp = chat_completion(
        model,
        [
            {"role": "system", "content": instruction},
            {"role": "user", "content": question},
        ],
        max_tokens=_MAX_ANSWER_TOKENS,
        temperature=0.0,
    )
    choice = resp["choices"][0]
    answer = (choice["message"].get("content") or "").strip()
    meta = {
        "provider_returned_model": resp.get("model"),
        "provider": resp.get("provider"),
        "finish_reason": choice.get("finish_reason"),
        "usage": _slim_usage(resp.get("usage")),
    }
    return answer, meta


def _call_deepseek(question: str, model: str, instruction: str) -> tuple[str, dict]:
    from desi.spl_adapter.deepseek_client import DeepSeekClient
    client = DeepSeekClient(model_id=model) if model else DeepSeekClient()
    raw = client.complete(f"{instruction}\n\nQuestion: {question}").raw_text
    data = json.loads(raw)
    choice = data["choices"][0]
    answer = (choice["message"].get("content") or "").strip()
    meta = {
        "provider_returned_model": data.get("model"),
        "finish_reason": choice.get("finish_reason"),
        "usage": _slim_usage(data.get("usage")),
    }
    return answer, meta


def _llm_answer(backend: str, question: str, model: str,
                instruction: str) -> tuple[str, str | None, dict]:
    """Return (answer, error, call_meta). Only called when backend is usable."""
    try:
        if backend == "hf":
            answer, meta = _call_hf(question, model, instruction)
        elif backend == "openrouter":
            answer, meta = _call_openrouter(question, model, instruction)
        elif backend == "deepseek":
            answer, meta = _call_deepseek(question, model, instruction)
        else:
            return "", f"unknown backend {backend!r}", {}
        return answer, None, meta
    except Exception as exc:  # network / parse / backend errors -> clean fallback
        return "", f"{backend} call failed: {exc!r}", {}


def raw_llm_answer(task: dict, *, backend: str = "auto", model: str | None = None,
                   prompt_mode: str = "strict", dry_run: bool = False) -> dict:
    """LLM-only baseline: same backend/model/prompt path, **no** DESi governance.

    Returns ``{model_answer, error, provider_meta}``. ``provider_meta`` carries
    only the technical provider fields (backend, requested/resolved/
    provider_returned model, provider, finish_reason, usage) — no governance,
    replay, or claim signals. Never raises.
    """
    _ensure_desi_importable()  # the OpenRouter/DeepSeek clients live in `desi`
    question = str(task.get("Question", ""))
    resolved = resolve_backend(backend, model)
    model_id = resolve_model(resolved, model)
    answer, error, call_meta = "", None, {}

    if resolved == "none":
        error = "no answer-generation backend (set a key or --backend/--model)"
    elif dry_run:
        error = f"dry-run: {resolved} LLM call skipped"
    elif not _backend_usable(resolved, model):
        error = f"{resolved} selected but not usable (missing API key/token or model)"
    else:
        answer, error, call_meta = _llm_answer(
            resolved, question, model_id, _instruction(prompt_mode)
        )

    provider_meta = {
        "backend": resolved,
        "requested_model": model,
        "resolved_model": model_id,
        "provider_returned_model": call_meta.get("provider_returned_model"),
        "provider": call_meta.get("provider"),
        "finish_reason": call_meta.get("finish_reason"),
        "usage": call_meta.get("usage"),
    }
    return {"model_answer": answer, "error": error, "provider_meta": provider_meta}


# --------------------------------------------------------------------------- #
# DESi governance / replay / claim signals (+ optional run_desi loop)
# --------------------------------------------------------------------------- #
def _desi_signals(task_id: str, question: str, model_answer: str,
                  backend: str, llm_error: str | None) -> dict:
    sig = {
        "version": "unknown",
        "governance_enabled": False,
        "replay_enabled": False,
        "claim_tracking_enabled": False,
        "run_desi_integrated": False,
        "run_desi_metrics": None,
        "audit": {
            "question": question,
            "model_answer": model_answer,
            "backend": backend,
            "replay_hash": None,
            "answer_claim_id": None,
            "error": llm_error,
        },
        "errors": [],
    }

    _ensure_desi_importable()
    try:
        import desi
        sig["version"] = getattr(desi, "__version__", "unknown")
    except Exception as exc:
        sig["errors"].append(f"desi import failed: {exc!r}")
        return sig

    # Replay kernel (pure stdlib): deterministic signature of the audit struct.
    try:
        from desi.core.replay_kernel import replay_hash
        sig["audit"]["replay_hash"] = replay_hash({
            "task_id": task_id, "question": question,
            "model_answer": model_answer, "backend": backend,
            "error": llm_error,
        })
        sig["replay_enabled"] = True
    except Exception as exc:
        sig["errors"].append(f"replay kernel: {exc!r}")

    # Governance core integrity (pure stdlib).
    try:
        from desi.core.governance_core import governance_intact
        sig["governance_enabled"] = bool(governance_intact())
    except Exception as exc:
        sig["errors"].append(f"governance core: {exc!r}")

    # Claim id of the answer (pure stdlib).
    try:
        from desi.self_audit.claim import ClaimKind, make_claim_id
        sig["audit"]["answer_claim_id"] = make_claim_id(
            f"gaia/{task_id}", 0, ClaimKind.HASH, "model_answer", model_answer
        )
        sig["claim_tracking_enabled"] = True
    except Exception as exc:
        sig["errors"].append(f"claim tracking: {exc!r}")

    # Full governance loop (needs pydantic-backed models): optional.
    try:
        from desi.models import Trajectory, TrajectoryStep
        from desi.runner import run_desi
        traj = Trajectory(
            trajectory_id=f"gaia/{task_id}",
            steps=[TrajectoryStep(
                loop_index=0, operator="T3",
                novel_claims=1 if model_answer else 0,
                dup_rate=0.0, question=question,
            )],
            en_events=[],
        )
        metrics = run_desi(traj)
        terminal = getattr(getattr(metrics, "failure", None), "terminal", None)
        sig["run_desi_metrics"] = {
            "n_steps": getattr(metrics, "n_steps", None),
            "n_en_events": getattr(metrics, "n_en_events", None),
            "terminal_failure_mode": str(terminal) if terminal else None,
        }
        sig["run_desi_integrated"] = True
    except ModuleNotFoundError as exc:
        sig["errors"].append(
            f"run_desi unavailable ({exc.name} missing); install with "
            "`pip install desi-governance` for the full governance loop"
        )
    except Exception as exc:
        sig["errors"].append(f"run_desi failed: {exc!r}")

    return sig


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def solve_gaia_task(task: dict, *, backend: str = "auto",
                    dry_run: bool = False, model: str | None = None,
                    prompt_mode: str = "strict",
                    skip_attachments: bool = False) -> dict:
    """Solve one GAIA task. Always returns a well-formed dict; never raises."""
    task_id = str(task.get("task_id", ""))
    question = str(task.get("Question", ""))
    requires_attachment = bool((task.get("file_name") or "").strip())

    # OpenRouter/DeepSeek clients live in the `desi` package, so the repo's src/
    # must be importable before the LLM call (not only later in _desi_signals).
    _ensure_desi_importable()

    resolved = resolve_backend(backend, model)
    model_id = resolve_model(resolved, model)
    model_answer = ""
    llm_error: str | None = None
    call_meta: dict = {}
    # "none" | "skipped" | "not_provided_to_model"
    attachment_status = "none"

    if requires_attachment and skip_attachments:
        # Do not call the model on attachment-dependent tasks: there is no file
        # reader yet, so a real answer would be a blind guess. Leave it empty.
        attachment_status = "skipped"
        llm_error = "skipped: task requires an attachment (--skip-attachments)"
    elif resolved == "none":
        llm_error = (
            "no answer-generation backend: set HF_TOKEN+HF_INFERENCE_MODEL, "
            "OPENROUTER_API_KEY, or DEEPSEEK_API_KEY (or pass --backend/--model), "
            "so no model_answer was produced"
        )
    elif dry_run:
        llm_error = (
            f"dry-run: {resolved} LLM call skipped "
            f"(usable={_backend_usable(resolved, model)}, model={model_id!r})"
        )
    elif not _backend_usable(resolved, model):
        llm_error = (
            f"{resolved} selected but not usable (missing API key/token or model)"
        )
    else:
        if requires_attachment:
            # The attachment's content is not passed to the model; the strict
            # prompt asks it to answer UNKNOWN rather than hallucinate.
            attachment_status = "not_provided_to_model"
        model_answer, llm_error, call_meta = _llm_answer(
            resolved, question, model_id, _instruction(prompt_mode)
        )

    sig = _desi_signals(task_id, question, model_answer, resolved, llm_error)

    if model_answer:
        solver = "desi_governed_llm" if sig["run_desi_integrated"] else "llm_only"
    else:
        solver = "desi_adapter_fallback"

    errors = list(sig["errors"])
    if llm_error:
        errors.append(llm_error)

    reasoning_trace = (
        f"{solver}: backend={resolved}, dry_run={dry_run}; DESi v{sig['version']} "
        f"(governance_intact={sig['governance_enabled']}, "
        f"replay={sig['replay_enabled']}, claim_tracking={sig['claim_tracking_enabled']}, "
        f"run_desi_integrated={sig['run_desi_integrated']}, "
        f"replay_hash={sig['audit']['replay_hash']}). "
        + ("Answer produced by the LLM backend and governed by DESi signals."
           if model_answer else
           "No answer produced (see error); DESi wiring still validated.")
    )

    desi_metadata = {
        "solver": solver,
        "backend": resolved,
        # Model resolution trace: what was asked for, what we sent, what the
        # provider actually served. requested_model is the raw --model (may be
        # None); resolved_model is what is sent; provider_returned_model is what
        # OpenRouter/HF reports back (e.g. a dated/version-pinned id).
        "requested_model": model,
        "resolved_model": model_id,
        "model": model_id,
        "provider_returned_model": call_meta.get("provider_returned_model"),
        "provider": call_meta.get("provider"),
        "finish_reason": call_meta.get("finish_reason"),
        "usage": call_meta.get("usage"),
        "prompt_mode": prompt_mode,
        "dry_run": dry_run,
        "desi_version_or_commit": sig["version"],
        "governance_enabled": sig["governance_enabled"],
        "replay_enabled": sig["replay_enabled"],
        "claim_tracking_enabled": sig["claim_tracking_enabled"],
        "run_desi_integrated": sig["run_desi_integrated"],
        "run_desi_metrics": sig["run_desi_metrics"],
        "requires_attachment": requires_attachment,
        "attachment_seen": requires_attachment,
        "attachment_status": attachment_status,
        "replay_signature": sig["audit"]["replay_hash"],
        "answer_claim_id": sig["audit"]["answer_claim_id"],
        "audit": sig["audit"],
    }
    if errors:
        desi_metadata["error"] = "; ".join(errors)

    return {
        "model_answer": model_answer,
        "reasoning_trace": reasoning_trace,
        "desi_metadata": desi_metadata,
    }


if __name__ == "__main__":
    demo = solve_gaia_task(
        {"task_id": "demo-0001", "Question": "What is 2+2?", "file_name": ""},
        backend="auto",
    )
    print(json.dumps(demo, indent=2, ensure_ascii=False))

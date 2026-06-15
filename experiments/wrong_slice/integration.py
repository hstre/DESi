"""Integration point for the existing live harness.

This is the ONLY surface the live harness needs to call. It does not run models,
does not produce results, and adds no parallel harness — it wires the matcher,
audit, result schema, and analysis into whatever runner already exists.

Lifecycle the live harness follows per (case, arm, repetition):

    1. Build the `correct` slice for the pass (your code).
    2. For a wrong arm, build a candidate and call `admit_wrong_slice(...)`.
       If it returns (False, report), DISCARD the candidate (it is already
       audited) and construct another — never patch it to pass.
    3. Run the model on the admitted slice (your code) and observe outcomes.
    4. Call `record(...)` to build a schema-valid RunResult.
    5. After all runs, call `analyse(...)` on the collected records.

Stdlib only.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Callable, IO

from analysis import run_paired_analysis
from audit import admit_or_audit
from result_schema import RunResult, validate_record
from slice_matcher import Slice, content_hash, default_token_count

PREREG = Path(__file__).resolve().parent / "PREREGISTRATION.md"


def prereg_hash(path: str | os.PathLike = PREREG) -> str:
    """SHA-256 of the frozen pre-registration, to stamp every result."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def admit_wrong_slice(
    correct: Slice,
    candidate: Slice,
    audit_sink: str | os.PathLike | IO[str],
    *,
    context: dict | None = None,
    token_count: Callable[[str], int] = default_token_count,
    token_tolerance: int = 0,
) -> tuple[bool, object]:
    """Gate + audit a candidate wrong slice. Returns (admitted, report).

    Pass your harness's real tokenizer as ``token_count`` (e.g. the
    model2vec/potion-base-8M tokenizer) so token-length matching is faithful.
    """
    return admit_or_audit(
        correct,
        candidate,
        audit_sink,
        context=context,
        token_count=token_count,
        token_tolerance=token_tolerance,
    )


def record(
    *,
    experiment_id: str,
    case_id: str,
    arm: str,
    repetition: int,
    seed: int,
    provider: str,
    model_id: str,
    decoding: dict,
    fed_slice: Slice | None,
    matcher_ok: bool | None,
    no_loop: bool,
    task_completed: bool,
    no_severe_role_adoption: bool,
    no_control_failure: bool,
    metrics: dict | None = None,
    ts: str = "",
) -> RunResult:
    """Build a schema-valid RunResult. Raises if the record is malformed.

    ``fed_slice`` is the slice actually given to the model (None for the raw
    arm). Its content hash is recorded so the run is reconstructable.
    """
    result = RunResult(
        experiment_id=experiment_id,
        prereg_hash=prereg_hash(),
        case_id=case_id,
        arm=arm,
        repetition=repetition,
        seed=seed,
        provider=provider,
        model_id=model_id,
        decoding=decoding,
        slice_hash=content_hash(fed_slice) if fed_slice is not None else "",
        matcher_ok=matcher_ok,
        no_loop=no_loop,
        task_completed=task_completed,
        no_severe_role_adoption=no_severe_role_adoption,
        no_control_failure=no_control_failure,
        metrics=metrics or {},
        ts=ts,
    )
    problems = validate_record(result.to_record())
    if problems:
        raise ValueError(f"invalid RunResult: {problems}")
    return result


def analyse(results: list[RunResult], *, delta: float, alpha: float = 0.05) -> dict:
    """Run the pre-registered paired analysis over collected records."""
    return run_paired_analysis(results, delta=delta, alpha=alpha)

"""Combine deterministic diagnostics with role-based LLM analyses.

Order of operations (per project charter):
    1. Load trajectory.
    2. Compute deterministic metrics.
    3. Invoke roles, in this fixed order:
       Trajectory Analyst -> Attractor Diagnostician -> EN Event Analyst
       -> Skeptical Auditor -> Report Synthesizer
    4. The Skeptical Auditor receives the previous three role outputs and is
       allowed to dissent.
    5. The Report Synthesizer receives ALL outputs and the deterministic
       metrics, and is constrained by `ROLE_REPORT_SYNTHESIZER` rules.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from .config import Config, load_config
from .deepseek_client import DeepSeekClient
from .diagnostics import DeterministicMetrics, compute_all
from .models import Trajectory
from .phase_detector import PhaseDetectionResult, detect_phases
from .roles import (
    ROLE_ATTRACTOR_DIAGNOSTICIAN,
    ROLE_EN_EVENT_ANALYST,
    ROLE_REPORT_SYNTHESIZER,
    ROLE_SKEPTICAL_AUDITOR,
    ROLE_TRAJECTORY_ANALYST,
    build_messages,
)

_LOG = logging.getLogger(__name__)


@dataclass
class RoleOutput:
    role: str
    content: str
    error: str | None = None


@dataclass
class MetaAnalysisResult:
    trajectory: Trajectory
    metrics: DeterministicMetrics
    phases: PhaseDetectionResult
    role_outputs: list[RoleOutput]
    llm_enabled: bool

    def role_by_name(self, name: str) -> RoleOutput | None:
        for r in self.role_outputs:
            if r.role == name:
                return r
        return None


def _summarize_metrics_for_llm(
    trajectory: Trajectory,
    metrics: DeterministicMetrics,
    phases: PhaseDetectionResult,
) -> str:
    """Render the deterministic findings as a compact text block.

    The LLM roles receive this block + a small JSON view of the trajectory.
    Keeping the payload modest avoids surprise token bills.
    """
    lines: list[str] = []
    lines.append(f"trajectory_id: {trajectory.trajectory_id}")
    lines.append(f"domain: {trajectory.domain or '-'}")
    lines.append(f"seed: {trajectory.seed or '-'}")
    lines.append(f"persona: {trajectory.persona or '-'}")
    lines.append(f"n_steps: {metrics.n_steps}")
    lines.append(f"n_en_events: {metrics.n_en_events}")

    lines.append("")
    lines.append("EN classifications:")
    for c in metrics.en_classifications:
        lines.append(
            f"  loop={c.loop_index} eni_novelty={c.eni_novelty:.2f} -> {c.label}"
        )

    lines.append("")
    lines.append("Novelty recoveries:")
    for r in metrics.novelty_recoveries:
        dd = "n/a" if r.dup_delta is None else f"{r.dup_delta:+.2f}"
        nc = "n/a" if r.novel_claims_next is None else r.novel_claims_next
        lines.append(
            f"  loop={r.loop_index} dup_delta={dd} "
            f"novel_claims_next={nc} recovered={r.recovered}"
        )

    lines.append("")
    p = metrics.penultimate
    lines.append("Penultimate-EN assessment:")
    lines.append(
        f"  has_candidate={p.has_candidate} penultimate_loop={p.penultimate_loop} "
        f"({p.penultimate_label}) last_loop={p.last_loop} ({p.last_label})"
    )
    lines.append(f"  note: {p.note}")

    a = metrics.attractor
    lines.append("")
    lines.append("Terminal attractor candidates (heuristic):")
    lines.append(f"  candidate_claim_ids={a.candidate_claim_ids}")
    lines.append(f"  method={a.method}; note={a.note}")

    f = metrics.failure
    lines.append("")
    lines.append("Failure modes:")
    lines.append(f"  terminal={f.terminal}")
    if f.per_step:
        for loop_idx, fm in f.per_step:
            lines.append(f"  loop={loop_idx} failure_mode={fm}")

    lines.append("")
    lines.append("Phase detection:")
    if not phases.phases:
        lines.append("  (no phase detected)")
    for ps in phases.phases:
        lines.append(
            f"  {ps.name} loops {ps.start_loop}..{ps.end_loop} "
            f"confidence={ps.confidence}"
        )
        for ev in ps.trigger_evidence:
            lines.append(f"    - {ev}")

    return "\n".join(lines)


def _trajectory_payload_for_llm(trajectory: Trajectory) -> str:
    """JSON snapshot of the trajectory passed to the LLM as evidence.

    `pydantic.BaseModel.model_dump` returns plain types we can json.dumps.
    """
    return json.dumps(trajectory.model_dump(mode="json"), indent=2, ensure_ascii=False)


def _safe_call(
    client: DeepSeekClient,
    role_name: str,
    role_prefix: str,
    user_payload: str,
) -> RoleOutput:
    try:
        content = client.chat(build_messages(role_prefix, user_payload))
        return RoleOutput(role=role_name, content=content)
    except Exception as exc:  # noqa: BLE001 — any failure becomes a role-output error
        _LOG.warning("Role %s failed: %s", role_name, exc)
        return RoleOutput(role=role_name, content="", error=str(exc))


def analyze(
    trajectory: Trajectory,
    *,
    use_llm: bool = True,
    config: Config | None = None,
    model_override: str | None = None,
) -> MetaAnalysisResult:
    """Run the full DESi meta-analysis pipeline."""
    cfg = config or load_config()
    metrics = compute_all(trajectory)
    phases = detect_phases(trajectory)

    if not use_llm:
        return MetaAnalysisResult(
            trajectory=trajectory,
            metrics=metrics,
            phases=phases,
            role_outputs=[],
            llm_enabled=False,
        )

    if model_override:
        cfg = Config(
            deepseek_api_key=cfg.deepseek_api_key,
            deepseek_base_url=cfg.deepseek_base_url,
            deepseek_model=model_override,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
            timeout_seconds=cfg.timeout_seconds,
            max_retries=cfg.max_retries,
        )

    client = DeepSeekClient(cfg)
    metrics_block = _summarize_metrics_for_llm(trajectory, metrics, phases)
    traj_block = _trajectory_payload_for_llm(trajectory)

    base_payload = (
        "## Deterministic metrics (authoritative)\n"
        f"{metrics_block}\n\n"
        "## Trajectory (JSON)\n"
        f"```json\n{traj_block}\n```\n"
    )

    outputs: list[RoleOutput] = []

    outputs.append(_safe_call(
        client, "TRAJECTORY_ANALYST", ROLE_TRAJECTORY_ANALYST, base_payload
    ))
    outputs.append(_safe_call(
        client, "ATTRACTOR_DIAGNOSTICIAN", ROLE_ATTRACTOR_DIAGNOSTICIAN, base_payload
    ))
    outputs.append(_safe_call(
        client, "EN_EVENT_ANALYST", ROLE_EN_EVENT_ANALYST, base_payload
    ))

    # Auditor sees deterministic metrics + previous three role outputs.
    auditor_payload = base_payload + "\n\n## Prior role outputs (subject to audit)\n"
    for r in outputs:
        body = r.error and f"[ERROR: {r.error}]" or r.content
        auditor_payload += f"\n### {r.role}\n{body}\n"
    outputs.append(_safe_call(
        client, "SKEPTICAL_AUDITOR", ROLE_SKEPTICAL_AUDITOR, auditor_payload
    ))

    # Synthesizer sees everything.
    synth_payload = base_payload + "\n\n## All role outputs\n"
    for r in outputs:
        body = r.error and f"[ERROR: {r.error}]" or r.content
        synth_payload += f"\n### {r.role}\n{body}\n"
    outputs.append(_safe_call(
        client, "REPORT_SYNTHESIZER", ROLE_REPORT_SYNTHESIZER, synth_payload
    ))

    return MetaAnalysisResult(
        trajectory=trajectory,
        metrics=metrics,
        phases=phases,
        role_outputs=outputs,
        llm_enabled=True,
    )

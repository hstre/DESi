"""Correction-packet actuator — a short, mechanical, status-bearing work-state the router prepends
ONLY at risk.

This is the lowest-risk way to make a guarded/recovery answer more stable: it does not touch hidden
states, logits, or weights, and it is not "another long system prompt". It is a compact (~100-300
token) packet built deterministically from the DesiReport — current valid state, invalidated/
superseded claims, open conflicts, and a fixed recovery target — that the router puts in front of the
prompt when, and only when, a risk condition holds. If it does not help, turn it off (it is a separate,
opt-in router mode); nothing about DESi changes.

Architecture: DESi delivers state/risks/invalidated/conflicts → the router decides packet yes/no
(``packet_applies``) → the packet steers the concrete answer (``build_correction_packet``) → the
verifier still decides whether a persistent update is allowed → Layer-9 stays the authority on state.
"""
from __future__ import annotations

from desi_router.governance.report import DesiReport

_HIGH = 0.7


def packet_applies(report: DesiReport, *, recovery_mode: bool = False,
                   verifier_failed_once: bool = False) -> bool:
    """Emit a correction packet ONLY at risk — never on clean cases (that would just add overhead and
    annoyance). The six trigger conditions from the spec, read off the report + its risk_scores."""
    r = report.risk_scores
    invalidated_claim_touched = bool(
        (report.invalidated_claim_ids or report.superseded_claim_ids) and report.task_touches_invalidated)
    open_conflict_touched = bool(report.open_conflict_ids and report.answer_requires_conflict_resolution)
    wrong_frame_risk_high = report.wrong_frame_present or r.get("bad_framing_nonrecovery", 0.0) >= _HIGH
    stale_confident_risk_high = r.get("stale_confident_answer", 0.0) >= _HIGH
    return bool(invalidated_claim_touched or open_conflict_touched or wrong_frame_risk_high
                or stale_confident_risk_high or recovery_mode or verifier_failed_once)


def _bullets(ids, texts, *, limit, suffix=""):
    out = []
    ids = list(ids) or [""] * len(list(texts))
    for cid, txt in list(zip(ids, texts, strict=False))[:limit]:
        tag = f"[{cid}] " if cid else ""
        body = (txt or "").strip().replace("\n", " ")
        out.append(f"- {tag}{body}{suffix}")
    return out


def build_correction_packet(report: DesiReport, *, max_chars: int = 1200,
                            per_section: int = 4) -> str:
    """Build the mechanical packet from the report. Short and status-bearing — not a discursive
    prompt. Capped so it can never grow into a long system prompt."""
    lines = ["EPISTEMIC CORRECTION PACKET"]

    if report.selected_claim_texts:
        lines.append("Current valid state:")
        lines += _bullets(report.selected_claim_ids, report.selected_claim_texts, limit=per_section)

    inval_ids = tuple(report.invalidated_claim_ids) + tuple(report.superseded_claim_ids)
    inval_txt = tuple(report.invalidated_claim_texts) + tuple(report.superseded_claim_texts)
    if inval_txt:
        lines.append("Invalidated / superseded — do NOT reuse as current fact:")
        lines += _bullets(inval_ids, inval_txt, limit=per_section)

    if report.open_conflict_texts:
        lines.append("Open conflict — do NOT close without new evidence:")
        lines += _bullets(report.open_conflict_ids, report.open_conflict_texts, limit=per_section)

    lines.append("Recovery target:")
    lines.append("- Answer from the current valid state.")
    lines.append("- If you mention superseded claims, mark them as superseded.")
    lines.append("- Do not treat rejected options as active decisions.")
    if report.wrong_frame_present:
        lines.append("- A wrong framing already entered the conversation — correct it against the "
                     "current state before answering.")

    packet = "\n".join(lines)
    if len(packet) > max_chars:                       # hard cap: trim trailing bullets, keep structure
        packet = packet[:max_chars].rsplit("\n", 1)[0] + "\n- (truncated)"
    return packet

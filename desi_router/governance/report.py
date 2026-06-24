"""Router-facing DESi report — a thin, read-only projection of DESi/Layer-9 diagnostics.

Architecture rule: **DESi diagnoses, the router acts.** This module never enforces, never mutates
state, never blocks. It translates DESi outputs into router-facing *signals* so the deterministic
mode selector (``modes.py``) can choose what to do.

Honest scoping (grounded in the actual code + the ablations):
  * The ``EpistemicGapSnapshot`` exposes OPEN conflicts, evidence gaps, open questions and provenance
    — a resolved conflict is simply absent. It does NOT track invalidated / superseded claims or an
    extraction confidence, so those are passed in EXPLICITLY by the caller (from Layer-9 status or an
    extraction step) and never invented here.
  * ``risk_scores`` are PRE-DECISION HEURISTICS computed deterministically from the signals above —
    they are NOT the post-hoc degeneration metrics from the ablation (those are measured on a
    finished answer by ``verifier.py``). Metadata governance is not claimed as a recall effect.

The snapshot is accepted duck-typed (any object with ``.conflicts`` / ``.provenance`` …) so the
router does not hard-depend on DESi core.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any

RISK_KEYS = ("invalid_claim_reuse", "bad_framing_nonrecovery", "coherence_without_continuity",
             "stale_confident_answer", "wrong_state_poisoning", "conflict_closure_risk")


@dataclass
class DesiReport:
    task_id: str
    user_id: str | None = None
    project_id: str | None = None
    selected_state_summary: str = ""
    selected_claim_ids: tuple[str, ...] = ()
    invalidated_claim_ids: tuple[str, ...] = ()
    superseded_claim_ids: tuple[str, ...] = ()
    open_conflict_ids: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()
    state_recall_estimate: float | None = None       # 0..1, optional
    extraction_confidence: float | None = None        # 0..1, optional
    has_usable_state: bool = False
    user_specific_missing: bool = False
    wrong_frame_present: bool = False                  # a wrong frame already entered the convo
    task_touches_invalidated: bool = False
    answer_requires_conflict_resolution: bool = False
    # claim TEXTS the post-answer verifier needs (not part of the published id-schema)
    selected_claim_texts: tuple[str, ...] = ()
    invalidated_claim_texts: tuple[str, ...] = ()
    superseded_claim_texts: tuple[str, ...] = ()
    open_conflict_texts: tuple[str, ...] = ()
    risk_scores: dict[str, float] = field(default_factory=dict)
    recommended_mode: str = ""
    explanation_for_router: str = ""
    audit_hash: str = ""

    def __post_init__(self) -> None:
        if not self.risk_scores:
            self.risk_scores = _risk_scores(self)
        if not self.audit_hash:
            self.audit_hash = self._hash()

    def _hash(self) -> str:
        body = {k: v for k, v in asdict(self).items() if k != "audit_hash"}
        return hashlib.sha256(
            json.dumps(body, sort_keys=True, ensure_ascii=False, default=list).encode("utf-8")
        ).hexdigest()

    def schema_dict(self) -> dict[str, Any]:
        """The published router-facing schema (id-lists + risk_scores), without the verifier texts."""
        d = asdict(self)
        for k in ("selected_claim_texts", "invalidated_claim_texts", "superseded_claim_texts",
                  "open_conflict_texts"):
            d.pop(k, None)
        return d


def _lo(v: float | None, default: float) -> float:
    return default if v is None else float(v)


def _astuple(x) -> tuple:
    """Coerce to a tuple, treating a bare string as a single element (not a char sequence)."""
    if x is None:
        return ()
    if isinstance(x, str):
        return (x,)
    return tuple(x)


def _risk_scores(r: DesiReport) -> dict[str, float]:
    """Deterministic PRE-DECISION risk heuristics in [0,1]. Documented as estimates, not the measured
    degeneration metrics. Higher = the router should be more cautious."""
    has_stale = bool(r.superseded_claim_ids)
    has_invalid = bool(r.invalidated_claim_ids or r.superseded_claim_ids)
    recall_low = _lo(r.state_recall_estimate, 1.0) < 0.5
    conf_low = _lo(r.extraction_confidence, 1.0) < 0.5

    invalid_reuse = 1.0 if (has_invalid and r.task_touches_invalidated) else (0.6 if has_invalid else 0.0)
    if not r.has_usable_state:
        poisoning = 0.0                                   # no state present -> nothing to poison
    elif conf_low or recall_low:
        poisoning = 0.8
    else:
        poisoning = 0.1
    stale = 0.8 if has_stale else (0.6 if (r.has_usable_state and recall_low) else 0.1)
    conflict = 1.0 if (r.open_conflict_ids and r.answer_requires_conflict_resolution) \
        else (0.5 if r.open_conflict_ids else 0.0)
    bad_framing = 0.9 if r.wrong_frame_present else (0.4 if poisoning >= 0.6 else 0.0)
    coherence = 0.6 if (r.has_usable_state and recall_low) else 0.2
    return {"invalid_claim_reuse": round(invalid_reuse, 2),
            "bad_framing_nonrecovery": round(bad_framing, 2),
            "coherence_without_continuity": round(coherence, 2),
            "stale_confident_answer": round(stale, 2),
            "wrong_state_poisoning": round(poisoning, 2),
            "conflict_closure_risk": round(conflict, 2)}


def report_from_snapshot(task_id: str, snapshot: Any, *,
                         selected_claim_ids: tuple[str, ...] = (),
                         selected_claim_texts: tuple[str, ...] = (),
                         invalidated_claim_ids: tuple[str, ...] = (),
                         invalidated_claim_texts: tuple[str, ...] = (),
                         superseded_claim_ids: tuple[str, ...] = (),
                         superseded_claim_texts: tuple[str, ...] = (),
                         extraction_confidence: float | None = None,
                         state_recall_estimate: float | None = None,
                         user_specific_missing: bool = False,
                         wrong_frame_present: bool = False,
                         task_touches_invalidated: bool = False,
                         answer_requires_conflict_resolution: bool = False,
                         user_id: str | None = None, project_id: str | None = None) -> DesiReport:
    """Project a (duck-typed) EpistemicGapSnapshot into a router-facing report. READ-ONLY: it never
    mutates the snapshot. Fields the snapshot does not track (invalidated/superseded/confidence) are
    supplied by the caller, never fabricated here."""
    conflicts = tuple(getattr(snapshot, "conflicts", ()) or ())
    prov = getattr(snapshot, "provenance", None)
    prov_refs = tuple(p for p in (getattr(prov, "snapshot_hash", "") or "",) if p)
    open_conflict_ids = tuple(getattr(c, "id", "") for c in conflicts)
    open_conflict_texts = tuple(
        f"{getattr(c, 'kind', '')} over {', '.join(getattr(c, 'scope', ()) or ())}".strip()
        for c in conflicts)
    return DesiReport(
        task_id=task_id, user_id=user_id, project_id=project_id,
        selected_claim_ids=_astuple(selected_claim_ids),
        selected_claim_texts=_astuple(selected_claim_texts),
        invalidated_claim_ids=_astuple(invalidated_claim_ids),
        invalidated_claim_texts=_astuple(invalidated_claim_texts),
        superseded_claim_ids=_astuple(superseded_claim_ids),
        superseded_claim_texts=_astuple(superseded_claim_texts),
        open_conflict_ids=open_conflict_ids, open_conflict_texts=open_conflict_texts,
        provenance_refs=prov_refs,
        state_recall_estimate=state_recall_estimate, extraction_confidence=extraction_confidence,
        has_usable_state=bool(selected_claim_ids),
        user_specific_missing=user_specific_missing, wrong_frame_present=wrong_frame_present,
        task_touches_invalidated=task_touches_invalidated,
        answer_requires_conflict_resolution=answer_requires_conflict_resolution,
        explanation_for_router=(
            f"{len(open_conflict_ids)} open conflict(s), "
            f"{len(invalidated_claim_ids) + len(superseded_claim_ids)} invalidated/superseded, "
            f"usable_state={bool(selected_claim_ids)}"))

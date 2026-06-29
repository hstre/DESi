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

from desi_router.governance.provenance import assess_provenance as _assess_provenance
from desi_router.governance.scope import scope_mismatches as _scope_mismatches

RISK_KEYS = ("invalid_claim_reuse", "bad_framing_nonrecovery", "coherence_without_continuity",
             "stale_confident_answer", "wrong_state_poisoning", "conflict_closure_risk",
             "missing_opposition", "thin_provenance", "scope_mismatch")


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
    # opposition the FULL-GRAPH scan holds for the selected claims but the slice did NOT surface —
    # the plausible-wrong-slice signal (see missing_opposition.py). Empty unless a scan supplied it.
    omitted_opposition_ids: tuple[str, ...] = ()
    # thin/old/all-derived provenance under the slice (provenance.py) and out-of-scope claim tags
    # (scope.py) — both plausible-wrong-slice families that opposition cannot see. Empty unless the
    # caller supplies provenance/scope facts, so existing reports are unchanged.
    provenance_under_support: bool = False
    provenance_reasons: tuple[str, ...] = ()
    scope_mismatch_scopes: tuple[str, ...] = ()
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
    omitted_opposition_texts: tuple[str, ...] = ()
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
                  "open_conflict_texts", "omitted_opposition_texts"):
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
    # the graph holds opposition the slice omitted -> the slice is plausible but one-sided. 0.0 when
    # the scan found nothing omitted, so every existing case (no scan) keeps its prior risk vector.
    missing_opp = 1.0 if r.omitted_opposition_ids else 0.0
    # under-support and scope mismatch are caution-grade (>= _MOD in modes.py), not guarded-grade:
    # the slice is under-determined / out of scope, not actively contradicted. 0.0 when absent.
    thin_prov = 0.6 if r.provenance_under_support else 0.0
    scope_mis = 0.6 if r.scope_mismatch_scopes else 0.0
    return {"invalid_claim_reuse": round(invalid_reuse, 2),
            "bad_framing_nonrecovery": round(bad_framing, 2),
            "coherence_without_continuity": round(coherence, 2),
            "stale_confident_answer": round(stale, 2),
            "wrong_state_poisoning": round(poisoning, 2),
            "conflict_closure_risk": round(conflict, 2),
            "missing_opposition": round(missing_opp, 2),
            "thin_provenance": round(thin_prov, 2),
            "scope_mismatch": round(scope_mis, 2)}


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
                         graph_opposition_ids: tuple[str, ...] = (),
                         graph_opposition_texts: tuple[str, ...] = (),
                         provenance_sources: tuple[str, ...] = (),
                         derived_flags: tuple[bool, ...] = (),
                         provenance_stale: bool = False,
                         task_scope: str | None = None,
                         claim_scopes: tuple[str, ...] = (),
                         user_id: str | None = None, project_id: str | None = None) -> DesiReport:
    """Project a (duck-typed) EpistemicGapSnapshot into a router-facing report. READ-ONLY: it never
    mutates the snapshot. Fields the snapshot does not track (invalidated/superseded/confidence) are
    supplied by the caller, never fabricated here.

    ``graph_opposition_ids``/``_texts`` are the result of a slice-INDEPENDENT full-graph scan for
    opposition to the selected claims (contradiction / supersession / open question). What of it the
    slice did not already surface becomes ``omitted_opposition_ids`` — the plausible-wrong-slice
    flag. Empty by default, so callers that do not run the scan get the exact prior behaviour.
    """
    conflicts = tuple(getattr(snapshot, "conflicts", ()) or ())
    prov = getattr(snapshot, "provenance", None)
    prov_refs = tuple(p for p in (getattr(prov, "snapshot_hash", "") or "",) if p)
    open_conflict_ids = tuple(getattr(c, "id", "") for c in conflicts)
    open_conflict_texts = tuple(
        f"{getattr(c, 'kind', '')} over {', '.join(getattr(c, 'scope', ()) or ())}".strip()
        for c in conflicts)
    # what the slice already surfaced; opposition the graph holds beyond this is "omitted"
    sel = _astuple(selected_claim_ids)
    surfaced = set(sel) | set(_astuple(invalidated_claim_ids)) | set(_astuple(superseded_claim_ids)) \
        | set(open_conflict_ids)
    opp_ids = _astuple(graph_opposition_ids)
    opp_texts = _astuple(graph_opposition_texts)
    omitted_pairs = [(oid, opp_texts[i] if i < len(opp_texts) else "")
                     for i, oid in enumerate(opp_ids) if oid and oid not in surfaced]
    omitted_ids = tuple(dict.fromkeys(oid for oid, _ in omitted_pairs))
    omitted_texts = tuple(t for _, t in omitted_pairs if t)
    # provenance-entropy + scope-match — the plausible-wrong-slice families opposition cannot see
    prov_assess = _assess_provenance(n_claims=len(sel), source_families=provenance_sources,
                                     derived_flags=derived_flags, stale=provenance_stale)
    scope_bad = _scope_mismatches(task_scope, _astuple(claim_scopes))
    return DesiReport(
        task_id=task_id, user_id=user_id, project_id=project_id,
        selected_claim_ids=_astuple(selected_claim_ids),
        selected_claim_texts=_astuple(selected_claim_texts),
        invalidated_claim_ids=_astuple(invalidated_claim_ids),
        invalidated_claim_texts=_astuple(invalidated_claim_texts),
        superseded_claim_ids=_astuple(superseded_claim_ids),
        superseded_claim_texts=_astuple(superseded_claim_texts),
        open_conflict_ids=open_conflict_ids, open_conflict_texts=open_conflict_texts,
        omitted_opposition_ids=omitted_ids, omitted_opposition_texts=omitted_texts,
        provenance_under_support=prov_assess["under_support"],
        provenance_reasons=prov_assess["reasons"], scope_mismatch_scopes=scope_bad,
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

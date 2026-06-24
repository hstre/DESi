"""State-integrity assessor — DESi's diagnosis step BEFORE the router acts.

The router benchmark exposed the load-bearing blind spot: the router protects against a plausible-wrong
slice only when DESi/Layer-9 *signals* it (Phase-2 concordance 1.00 signaled vs 0.00 unsignaled). The
honest response is NOT to make the router cleverer — it is to convert as much of that blind spot as
possible into a DETERMINISTIC structural signal, and to make the irreducible remainder degrade to
caution rather than pretend to detect it.

This module is that signal producer. It reads structural facts only (Layer-9 invalid/supersede status,
provenance, scope, relevance) and emits a verdict the router consumes:

    state_integrity      ∈ {clean, stale, contradictory, suspicious, irrelevant, uncertain}
    state_mismatch_risk  ∈ [0,1]
    basis                ∈ {deterministic_flag, calibrated_caution, no_flag}

Crucial honesty: it NEVER certifies the slice is *correct*. A ``clean`` verdict means "no structural
red flag fired" (absence of evidence), not "this is right" — ``basis='no_flag'``. The genuinely
plausible-wrong slice that matches provenance, is relevant, carries no Layer-9 status and contradicts
nothing is undetectable here by construction; the only honest move for it is calibrated caution when
ANY secondary doubt exists (borderline relevance / unknown confidence), else it is an acknowledged miss.

LLM for language, rules for logic: every check below is deterministic. No model decides integrity.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

CLEAN = "clean"
STALE = "stale"
CONTRADICTORY = "contradictory"
SUSPICIOUS = "suspicious"
IRRELEVANT = "irrelevant"
UNCERTAIN = "uncertain"

_DETERMINISTIC = (STALE, CONTRADICTORY, SUSPICIOUS, IRRELEVANT)

_TOK = re.compile(r"[a-z0-9][a-z0-9\-]+")
_STOP = frozenset((
    "the a an of to in on and or is are was were be been being that this these those it its as at by "
    "for with from has have had do does did but if then so what which who when where how we you i our "
    "your should would could can will now use using current value set per about into out".split()))
_REL_OK = 0.5            # >= clearly relevant
_REL_LOW = 0.2           # < clearly irrelevant; between the two is borderline -> caution


def _toks(s: str) -> set:
    return {t for t in _TOK.findall((s or "").lower()) if t not in _STOP and len(t) > 2}


def _coverage(question: str, slice_texts) -> float:
    """Fraction of the question's content tokens that the slice covers. A relevance proxy, not truth."""
    q = _toks(question)
    if not q:
        return 1.0
    s = set().union(*(_toks(t) for t in slice_texts)) if slice_texts else set()
    return len(q & s) / len(q)


def task_touches_conflict(question: str, conflict_scopes: tuple[tuple[str, ...], ...]) -> bool:
    """Deterministic: does the TASK ask to resolve an open Layer-9 conflict? (question ↔ scope overlap).
    This is a task property, orthogonal to slice integrity — it is what tells the router to keep an
    open conflict OPEN rather than let the answer silently close it."""
    qt = _toks(question)
    for scope in conflict_scopes:
        st = set().union(*(_toks(s) for s in scope)) if scope else set()
        if st and len(st & qt) / len(st) >= 0.5:
            return True
    return False


@dataclass
class StateIntegrity:
    label: str
    state_mismatch_risk: float
    basis: str                                   # deterministic_flag | calibrated_caution | no_flag
    reasons: tuple[str, ...] = ()
    signals: dict = field(default_factory=dict)

    @property
    def certifies_correctness(self) -> bool:
        return False                             # by construction — never; absence of a flag is not proof


def assess_state_integrity(
    *, question: str,
    slice_claim_ids: tuple[str, ...] = (),
    slice_claim_texts: tuple[str, ...] = (),
    layer9_invalidated_ids: tuple[str, ...] = (),
    layer9_superseded_ids: tuple[str, ...] = (),
    conflict_scopes: tuple[tuple[str, ...], ...] = (),
    slice_project: str | None = None, context_project: str | None = None,
    slice_user: str | None = None, context_user: str | None = None,
    extraction_confidence: float | None = None,
) -> StateIntegrity:
    """Deterministic structural integrity of a candidate slice w.r.t. the task. Ordered
    most-severe-first; the first firing check wins."""
    ids = set(slice_claim_ids)
    reasons: list[str] = []
    sig: dict = {}

    # 1. STALE — a slice claim carries Layer-9 invalid/supersede status (a lookup, not detection).
    stale_ids = ids & (set(layer9_invalidated_ids) | set(layer9_superseded_ids))
    sig["stale_ids"] = sorted(stale_ids)
    if stale_ids:
        return StateIntegrity(STALE, 0.9, "deterministic_flag",
                              (f"slice claims {sorted(stale_ids)} are invalidated/superseded in Layer-9",),
                              sig)

    # 2. CONTRADICTORY — a slice claim overlaps the scope of a currently-open Layer-9 conflict.
    cov = _coverage(question, slice_claim_texts)
    sig["relevance"] = round(cov, 3)
    slice_tok = set().union(*(_toks(t) for t in slice_claim_texts)) if slice_claim_texts else set()
    for scope in conflict_scopes:
        st = set().union(*(_toks(s) for s in scope)) if scope else set()
        if st and len(st & slice_tok) / len(st) >= 0.5:
            sig["conflict_scope"] = list(scope)
            return StateIntegrity(CONTRADICTORY, 0.85, "deterministic_flag",
                                  (f"slice touches an open conflict scope {list(scope)}",), sig)

    # 3. SUSPICIOUS — provenance mismatch: the slice is from another project/user than the task's.
    prov_mismatch = ((slice_project and context_project and slice_project != context_project)
                     or (slice_user and context_user and slice_user != context_user))
    if prov_mismatch:
        sig["provenance"] = {"slice_project": slice_project, "context_project": context_project,
                             "slice_user": slice_user, "context_user": context_user}
        return StateIntegrity(SUSPICIOUS, 0.8, "deterministic_flag",
                              ("slice provenance (project/user) does not match the task context",), sig)

    # 4. IRRELEVANT — the slice does not cover the question's content terms.
    if slice_claim_ids and cov < _REL_LOW:
        return StateIntegrity(IRRELEVANT, 0.7, "deterministic_flag",
                              (f"slice covers only {cov:.0%} of the question's content terms",), sig)

    # 5. UNCERTAIN — the irreducible zone: no hard flag, but a secondary doubt exists. Degrade to
    #    caution rather than claim the slice is fine (this is the honest handling of plausible-wrong).
    conf_low = extraction_confidence is not None and extraction_confidence < 0.6
    borderline = bool(slice_claim_ids) and _REL_LOW <= cov < _REL_OK
    if conf_low or borderline:
        if conf_low:
            reasons.append(f"extraction confidence {extraction_confidence} is low/uncertain")
        if borderline:
            reasons.append(f"relevance {cov:.0%} is borderline (not clearly on-topic)")
        return StateIntegrity(UNCERTAIN, 0.45, "calibrated_caution", tuple(reasons), sig)

    # 6. CLEAN — no structural red flag. NOT a certificate of correctness (basis='no_flag').
    return StateIntegrity(CLEAN, 0.1, "no_flag",
                          ("no structural red flag (status/provenance/scope/relevance all pass) — "
                           "this does NOT certify the slice is correct",), sig)


def integrity_report_kwargs(integrity: StateIntegrity, *,
                            slice_claim_ids: tuple[str, ...], slice_claim_texts: tuple[str, ...],
                            stale_ids: tuple[str, ...] = ()) -> dict:
    """Translate an integrity verdict into report_from_snapshot kwargs, so the router's select_mode
    routes accordingly. The mapping is the bridge: DESi diagnoses (here) -> the router acts (select_mode).
    """
    label = integrity.label
    if label == STALE:
        stale = tuple(stale_ids) or slice_claim_ids
        return dict(selected_claim_ids=slice_claim_ids, selected_claim_texts=slice_claim_texts,
                    invalidated_claim_ids=stale, invalidated_claim_texts=slice_claim_texts,
                    task_touches_invalidated=True, extraction_confidence=0.9, state_recall_estimate=1.0)
    if label == CONTRADICTORY:
        return dict(selected_claim_ids=slice_claim_ids, selected_claim_texts=slice_claim_texts,
                    answer_requires_conflict_resolution=True, extraction_confidence=0.9,
                    state_recall_estimate=1.0)
    if label == SUSPICIOUS:
        return dict(selected_claim_ids=slice_claim_ids, selected_claim_texts=slice_claim_texts,
                    user_specific_missing=True)
    if label == IRRELEVANT:
        # an irrelevant slice is effectively no usable state -> retrieve real evidence (and verify)
        return dict(selected_claim_ids=())
    if label == UNCERTAIN:
        # calibrated caution: keep the slice but force guarded + a verifier (low recall signal)
        return dict(selected_claim_ids=slice_claim_ids, selected_claim_texts=slice_claim_texts,
                    extraction_confidence=0.3, state_recall_estimate=0.4)
    return dict(selected_claim_ids=slice_claim_ids, selected_claim_texts=slice_claim_texts,
                extraction_confidence=0.95, state_recall_estimate=1.0)

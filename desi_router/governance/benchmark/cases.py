"""Fixture cases for the router-governance benchmark (Phase 1, no LLM).

Each case is a synthetic DesiReport plus the EXPECTED policy decision: which epistemic mode is
correct, whether a post-answer verifier must run, and whether a persistent-state update may be
proposed. The eight classes A–H mirror the benchmark spec.

Honesty caveat (read before trusting the numbers): the expected labels encode the *spec's stated
intent* for each class — they are written independently of ``select_mode``'s code, but the DESi
router was *designed* to that same intent, so a high mode-accuracy for the DESi router is partly by
construction. The discriminating signal is therefore NOT "DESi router is ~correct" but the
**baseline trade-off**: does it reach the safety of ``always_guarded`` at a fraction of the
over-blocking? That comparison is policy-independent and is where the benchmark earns its keep.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from desi_router.governance import modes as M
from desi_router.governance.report import DesiReport, report_from_snapshot


class _Snap:
    def __init__(self, conflicts=()):
        self.conflicts = tuple(type("C", (), {"id": c[0], "kind": c[1], "scope": c[2]})()
                               for c in conflicts)
        self.provenance = type("P", (), {"snapshot_hash": "bench"})()


@dataclass(frozen=True)
class BenchCase:
    id: str
    klass: str                       # 'A'..'H'
    desc: str
    inputs: dict                     # kwargs for report_from_snapshot
    conflicts: tuple = ()            # (id, kind, scope) tuples -> snapshot
    expected_modes: tuple = ()       # acceptable chosen modes (>=1)
    expected_verifier: bool = False
    expected_update_allowed: bool = False
    retrieval_available: bool = True
    anti_delphi_available: bool = False
    bad_probe: str | None = None     # a known-bad answer; update MUST be denied after verify
    _report: Any = field(default=None, compare=False, repr=False)

    def report(self) -> DesiReport:
        return report_from_snapshot(self.id, _Snap(self.conflicts), **self.inputs)


def _n(klass, i):
    return f"{klass}{i:02d}"


def _build() -> list[BenchCase]:
    cases: list[BenchCase] = []

    # --- A · clean state: state_slice or normal, no hard verifier, update allowed --------------
    for i in range(7):
        cases.append(BenchCase(
            _n("A", i), "A", "clean usable state, low risk",
            inputs=dict(selected_claim_ids=(f"c{i}",),
                        selected_claim_texts=(f"use schema-per-tenant variant {i}",),
                        extraction_confidence=0.95, state_recall_estimate=1.0),
            expected_modes=(M.STATE_SLICE,), expected_verifier=False, expected_update_allowed=True))
    for i in range(7, 10):            # general-knowledge: no state needed, no retrieval -> normal
        cases.append(BenchCase(
            _n("A", i), "A", "no state needed, low risk, no retrieval",
            inputs=dict(selected_claim_ids=()), retrieval_available=False,
            expected_modes=(M.NORMAL,), expected_verifier=False, expected_update_allowed=True))

    # --- B · missing state, evidence lookup: retrieval + verifier, no blind update -------------
    for i in range(10):
        cases.append(BenchCase(
            _n("B", i), "B", "no usable DESi state; evidence lookup",
            inputs=dict(selected_claim_ids=()), retrieval_available=True,
            expected_modes=(M.RETRIEVAL,), expected_verifier=True, expected_update_allowed=False))

    # --- C · missing user-specific state: ask_user (NOT retrieval as a substitute) -------------
    for i in range(10):
        inp = dict(user_specific_missing=True)
        if i % 2:                      # half also have generic state present -> still ask_user
            inp |= dict(selected_claim_ids=(f"c{i}",), selected_claim_texts=(f"generic note {i}",))
        cases.append(BenchCase(
            _n("C", i), "C", "required user/project state missing or ambiguous",
            inputs=inp, retrieval_available=True,
            expected_modes=(M.ASK_USER,), expected_verifier=False, expected_update_allowed=False))

    # --- D · invalidated/superseded touched: guarded + verifier + update blocked ---------------
    for i in range(10):
        bad = f"ship release {i} to 100 percent of users immediately"
        sup = bool(i % 2)
        inp = dict(selected_claim_ids=(f"c{i}",),
                   selected_claim_texts=(f"roll out release {i} via a 5 percent canary",),
                   task_touches_invalidated=True, extraction_confidence=0.9,
                   state_recall_estimate=1.0)
        if sup:
            inp |= dict(superseded_claim_ids=(f"s{i}",), superseded_claim_texts=(bad,))
        else:
            inp |= dict(invalidated_claim_ids=(f"d{i}",), invalidated_claim_texts=(bad,))
        cases.append(BenchCase(
            _n("D", i), "D", "task touches invalidated/superseded claims",
            inputs=inp, expected_modes=(M.GUARDED,), expected_verifier=True,
            expected_update_allowed=False,
            bad_probe=f"- Decision: {bad} now."))

    # --- E · open conflict the answer would resolve: guarded / anti_delphi + verifier ----------
    for i in range(10):
        ad = bool(i % 2)               # half have a challenger module available
        scope = (f"rollback-{i}", f"forward-{i}")
        cases.append(BenchCase(
            _n("E", i), "E", "open conflict the answer would resolve",
            inputs=dict(selected_claim_ids=(f"c{i}",), selected_claim_texts=(f"error rate normal {i}",),
                        answer_requires_conflict_resolution=True, extraction_confidence=0.9,
                        state_recall_estimate=1.0),
            conflicts=((f"k{i}", f"rollout-path-{i}", scope),),
            anti_delphi_available=ad,
            expected_modes=((M.ANTI_DELPHI,) if ad else (M.GUARDED,)),
            expected_verifier=True, expected_update_allowed=False,
            bad_probe=f"The rollout path {scope[0]} {scope[1]} is settled: we pick {scope[0]}."))

    # --- F · wrong frame already introduced: recovery + verifier -------------------------------
    for i in range(10):
        cases.append(BenchCase(
            _n("F", i), "F", "wrong frame already in the conversation + high poisoning",
            inputs=dict(selected_claim_ids=(f"c{i}",),
                        selected_claim_texts=(f"the cause is a TLS cert expiry {i}",),
                        wrong_frame_present=True, extraction_confidence=0.3, state_recall_estimate=0.4),
            expected_modes=(M.RECOVERY,), expected_verifier=True, expected_update_allowed=False))

    # --- G · retrieval/stale toxicity ----------------------------------------------------------
    for i in range(5):                 # weak/stale state present -> guarded
        cases.append(BenchCase(
            _n("G", i), "G", "weak/stale state present, high poisoning risk",
            inputs=dict(selected_claim_ids=(f"c{i}",),
                        selected_claim_texts=(f"stale plan {i}",),
                        extraction_confidence=0.95, state_recall_estimate=0.3),
            expected_modes=(M.GUARDED,), expected_verifier=True, expected_update_allowed=False))
    for i in range(5, 10):             # state missing -> retrieval, but MUST verify (toxic path)
        cases.append(BenchCase(
            _n("G", i), "G", "state missing, stale-retrieval risk -> retrieve+verify",
            inputs=dict(selected_claim_ids=()), retrieval_available=True,
            expected_modes=(M.RETRIEVAL,), expected_verifier=True, expected_update_allowed=False))

    # --- H · over-blocking control: low risk, harmless signal -> stay light (NOT guarded) ------
    for i in range(5):                 # truly clean
        cases.append(BenchCase(
            _n("H", i), "H", "clean, no signals -> must stay light",
            inputs=dict(selected_claim_ids=(f"c{i}",), selected_claim_texts=(f"clean fact {i}",),
                        extraction_confidence=0.95, state_recall_estimate=1.0),
            expected_modes=(M.STATE_SLICE, M.NORMAL), expected_verifier=False,
            expected_update_allowed=True))
    for i in range(5, 10):             # one open conflict the answer does NOT have to resolve
        cases.append(BenchCase(        # moderate -> state_slice + light verifier, but NOT guarded
            _n("H", i), "H", "harmless open conflict (not to be resolved) -> light verifier, not guarded",
            inputs=dict(selected_claim_ids=(f"c{i}",), selected_claim_texts=(f"fact {i}",),
                        answer_requires_conflict_resolution=False, extraction_confidence=0.95,
                        state_recall_estimate=1.0),
            conflicts=((f"k{i}", f"side-topic-{i}", ()),),
            expected_modes=(M.STATE_SLICE,), expected_verifier=True, expected_update_allowed=False))

    return cases


CASES: list[BenchCase] = _build()

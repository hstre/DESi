"""Semantic pre-solver mode router (PERIPHERAL).

Given ONE benchmark item (claim, evidence, optional question), choose the solver
PROMPT MODE -- baseline / evidence_strict / entailment_direct -- from the item's
epistemic structure, BEFORE the solver runs. DESi does NOT answer the item and
never emits SUPPORTS/REFUTES/NOT_ENOUGH_INFO; it only selects the solver policy.

The router projects each item through EXISTING, public, deterministic DESi
semantic-flow components -- no LLM, no network, no gold label, no dataset name:

  * desi.frames.FrameDetector                  -- frame of the claim and of the
                                                  evidence (substring/marker rule)
  * desi.frame_tension_integration.FrameTensionRouter
                                               -- claim-vs-evidence frame
                                                  consistency (CONFIRMED / TENSION
                                                  / CONFLICT / UNDECIDABLE)
  * desi.logic.LogicalAuditor                  -- logical state of the claim, and
                                                  of the 'evidence therefore claim'
                                                  entailment probe (proof / gap /
                                                  bridge / reject)

It only READS/PROJECTS through the core; it modifies no core module. It is
deterministic and replay-stable: identical (claim, evidence) -> identical mode.
A fixed timestamp is passed to the frame-tension router so even its ledger
receipt is reproducible (the routing fields read here are pure functions of the
text regardless).

This is a peripheral sequencer, not a new ontology and not a new meaning space:
it reuses the existing frame / logic / frame-tension machinery to pick a policy.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from desi.frame_tension import FrameConsistency  # noqa: E402
from desi.frame_tension_integration.router import FrameTensionRouter  # noqa: E402
from desi.frames import FrameDetector  # noqa: E402
from desi.logic import LogicalAuditor, LogicalState  # noqa: E402

MODES = ("baseline", "evidence_strict", "entailment_direct")
_FIXED_TS = datetime(2020, 1, 1, tzinfo=timezone.utc)  # determinism for the ledger


@dataclass(frozen=True)
class RouteResult:
    mode: str               # one of MODES
    features: dict          # the DESi semantic features used (serialisable)
    reason: str             # human-readable routing rationale


class SemanticModeRouter:
    """Deterministic pre-solver router. No LLM, no gold labels, no dataset name."""

    def __init__(self) -> None:
        self._detector = FrameDetector()
        self._auditor = LogicalAuditor()
        self._ften = FrameTensionRouter()

    def features(self, claim: str, evidence: str) -> dict:
        c = (claim or "").strip()
        e = (evidence or "").strip()
        claim_frame = self._detector.detect(claim_id="route-claim", source_text=c).frame_kind
        evid_frame = self._detector.detect(claim_id="route-evid", source_text=e).frame_kind
        routing = self._ften.route(
            claim_id="route", claim_text=c, inherited_context_text=e, recorded_at=_FIXED_TS)
        claim_audit = self._auditor.audit(c, claim_id="route-claim")
        # entailment probe: does an explicit 'evidence -> claim' chain resolve?
        chain_audit = self._auditor.audit(f"{e}. Therefore, {c}", claim_id="route-chain")
        return {
            "claim_frame": claim_frame.value,
            "evidence_frame": evid_frame.value,
            "frame_consistency": routing.consistency.value,
            "routed_pipeline": routing.routed_pipeline.value if routing.routed_pipeline else None,
            "claim_state": claim_audit.state.value,
            "claim_gap": claim_audit.gap.kind.value if claim_audit.gap else None,
            "chain_state": chain_audit.state.value,
            "chain_gap": chain_audit.gap.kind.value if chain_audit.gap else None,
            "chain_rule": chain_audit.rule.value if chain_audit.rule else None,
            # enum objects retained for the decision; stripped before serialising
            "_consistency": routing.consistency,
            "_claim_state": claim_audit.state,
            "_chain_state": chain_audit.state,
        }

    def route(self, claim: str, evidence: str, question: str | None = None) -> RouteResult:
        del question  # verify task uses claim+evidence; kept for the interface
        f = self.features(claim, evidence)
        cons, cstate = f["_consistency"], f["_claim_state"]
        chstate = f["_chain_state"]

        # Decision uses ONLY the item-level signals that actually discriminate
        # (verified empirically): frame consistency and claim authority-grounding.
        # The 'evidence -> claim' formal-inference probe is recorded as a feature
        # but is NOT routed on: on natural-language NLI/verification text it is
        # non-discriminative (it returns UNREACHABLE for ~all pairs because the
        # five formal inference rules do not match free-text entailment). The one
        # exception kept is an explicit positive proof (LOGICALLY_SUPPORTED),
        # which is rare but principled.

        # 1. claim grounded only by authority (or unreachable as a claim) -> the
        #    logic layer refuses to promote authority -> over-commitment risk ->
        #    require explicit evidence.
        if cstate is LogicalState.LOGICALLY_REJECTED:
            mode = "evidence_strict"
            reason = (f"claim logically rejected ({f['claim_state']}, gap "
                      f"{f['claim_gap']}: authority not self-supporting) -> evidence-strict")
        # 2. claim & evidence are in conflicting frames -> a naive entailment read
        #    is unsafe -> require explicit evidence.
        elif cons is FrameConsistency.CONFLICT:
            mode = "evidence_strict"
            reason = (f"claim/evidence frame CONFLICT "
                      f"({f['claim_frame']} vs {f['evidence_frame']}) -> evidence-strict")
        # 3. claim & evidence frames CONFIRMED coherent -> the comparison is
        #    well-posed -> take the entailment at face value (do not over-abstain).
        elif cons is FrameConsistency.CONFIRMED:
            mode = "entailment_direct"
            reason = (f"claim & evidence frames CONFIRMED coherent "
                      f"({f['claim_frame']}/{f['evidence_frame']}) -> entailment-direct")
        # 4. explicit positive proof of 'evidence -> claim' (rare) -> entailment.
        elif chstate is LogicalState.LOGICALLY_SUPPORTED:
            mode = "entailment_direct"
            reason = (f"evidence->claim resolves via inference rule "
                      f"{f['chain_rule']} -> entailment-direct")
        # 5. frame TENSION (inheritance blocked) -> require explicit evidence.
        elif cons is FrameConsistency.TENSION:
            mode = "evidence_strict"
            reason = ("claim/evidence frame TENSION (inheritance blocked) -> evidence-strict")
        # 6. no decisive structural signal (UNDECIDABLE, no proof) -> baseline.
        else:
            mode = "baseline"
            reason = (f"no decisive structure (consistency {f['frame_consistency']}, "
                      f"claim {f['claim_state']}) -> baseline")

        feats = {k: v for k, v in f.items() if not k.startswith("_")}
        return RouteResult(mode=mode, features=feats, reason=reason)


__all__ = ["MODES", "RouteResult", "SemanticModeRouter"]

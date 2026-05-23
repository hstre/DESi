"""Aufgabe 1 — extract per-state vectors for every trajectory.

A claim trajectory has five canonical states corresponding to
the five DESi pipeline layers it traverses:

    s0 = raw input (no processing)
    s1 = after PremiseExtractor
    s2 = after FrameDetector + FrameTensionLayer
    s3 = after FrameTensionRouter
    s4 = after LogicalAuditor

Four transitions per chain, plus the sample_trajectories file
contributes its own multi-step investigation trajectories.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from hashlib import sha256
from typing import Any


def _stable_frame_id(operator: str) -> int:
    """Seed-independent integer in [0, 9) derived
    from a sha256 hash of the operator string. The
    earlier version called Python's built-in
    ``hash()`` which is salted per-process via
    PYTHONHASHSEED, producing the v3.96a jitter
    on sample trajectory frame_id values. Fixed in
    v3.96c."""
    digest = sha256(operator.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % 9

from ..benchmark_multistep import ALL_MULTISTEP_CASES
from ..causal_naturalness.negative_control import (
    ALL_NC_CHAINS as V318_NC_CHAINS,
    NCShape,
)
from ..causal_redteam.cases import ALL_ADVERSARIAL_CASES
from ..frame_tension import FrameTensionLayer
from ..frame_tension_integration import FrameTensionRouter
from ..frames import FrameDetector, FrameKind
from ..heldout_causal import ALL_HELDOUT_CASES
from ..logic.audit import LogicalAuditor, LogicalState
from ..logic.inference import InferenceRule
from ..logic.premises import PremiseKind
from .state import StateVector, TrajectorySource


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


_FRAME_CODE: dict[FrameKind, float] = {
    FrameKind.FRAME_UNDECLARED:              0.0,
    FrameKind.THERMODYNAMIC:                 1.0,
    FrameKind.INFORMATION_THEORETIC:         2.0,
    FrameKind.ONTOLOGICAL_DISTINGUISHABILITY: 3.0,
    FrameKind.METAPHORICAL:                  4.0,
    FrameKind.FORMAL_LOGIC:                  5.0,
    FrameKind.EMPIRICAL_CAUSAL:              6.0,
    FrameKind.AUTHORITY_SPEECH:              7.0,
    FrameKind.TOOL_COMPUTABLE:               8.0,
}

_STATE_CODE: dict[LogicalState, float] = {
    LogicalState.UNDER_LOGICAL_AUDIT:  0.0,
    LogicalState.GAP_DETECTED:         1.0,
    LogicalState.BRIDGE_REQUIRED:      2.0,
    LogicalState.LOGICALLY_REJECTED:   3.0,
    LogicalState.LOGICALLY_SUPPORTED:  4.0,
}

_ROUTE_CODE: dict[str, float] = {
    "tool_gate": 1.0, "logical_auditor": 2.0,
    "consilium": 3.0, "reject": 0.5,
}


def _negation_count(text: str) -> int:
    low = " " + text.lower() + " "
    markers = (" not ", "n't ", " never ", " none ", " no ",
               " lacked ", " absent ", " vanished ", " missing ")
    return sum(low.count(m) for m in markers)


def _authority_count(text: str) -> int:
    low = " " + text.lower() + " "
    markers = (" says ", " said ", " states ", " stated ",
               " wrote ", " writes ", " argued ", " noted ",
               " thought ", " felt ", " suggested ", " believed ",
               " according to ", " concluded ", " announced ")
    return sum(low.count(m) for m in markers)


def _marker_density(text: str) -> float:
    tokens = max(1, len(text.split()))
    low = " " + text.lower() + " "
    markers = (
        " all ", " every ", " some ", " any ", " each ",
        " is a ", " is an ", " like a ", " as if ",
        " not ", "n't ", " never ", " no ",
        " because ", " depends on ", " requires ",
        " says ", " said ", " stated ", " wrote ", " argued ",
        " noted ", " felt ", " thought ", " consistently ",
        " universally ", " throughout ", " invariably ",
        " rests on ", " stems from ", " comes from ",
    )
    count = sum(low.count(m) for m in markers)
    return round(count / tokens, 6)


@dataclass(frozen=True)
class Trajectory:
    trajectory_id: str
    source: TrajectorySource
    text: str
    states: tuple[StateVector, ...]
    expected_natural: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "trajectory_id": self.trajectory_id,
            "source": self.source.value,
            "text": self.text,
            "states": [s.to_dict() for s in self.states],
            "expected_natural": self.expected_natural,
        }


def _claim_trajectory(
    trajectory_id: str, text: str, source: TrajectorySource,
    expected_natural: bool, *,
    auditor: LogicalAuditor, detector: FrameDetector,
    layer: FrameTensionLayer, router: FrameTensionRouter,
) -> Trajectory:
    """Build a five-state trajectory by pulling values from each
    DESi pipeline layer in sequence."""
    # s0 — raw input
    contradiction = float(_negation_count(text))
    anchor = _marker_density(text)
    source_q = float(_authority_count(text))
    s0 = StateVector(
        frame_id=0.0, contradiction_load=contradiction,
        anchor_density=anchor, source_quality=source_q,
        novelty=0.0, confidence=0.0,
        branch_cost=0.0, support_state=0.0, routing_state=0.0,
    )

    # s1 — after PremiseExtractor (we re-use the auditor's
    # internal extractor by running audit() but only reading the
    # propositions object).
    audit_result = auditor.audit(text)
    premises = audit_result.propositions.premises
    branch = float(len(premises))
    # Novelty of s1 vs s0: change in branch_cost.
    s1 = StateVector(
        frame_id=0.0, contradiction_load=contradiction,
        anchor_density=anchor, source_quality=source_q,
        novelty=branch,  # initial branch enumeration is "novelty"
        confidence=0.0,
        branch_cost=branch, support_state=0.0, routing_state=0.0,
    )

    # s2 — after FrameDetector + FrameTensionLayer.
    frame_decl = detector.detect(
        claim_id=trajectory_id, source_text=text,
    )
    frame_code = _FRAME_CODE.get(frame_decl.frame_kind, 0.0)
    layer_decision = layer.gate(
        claim_id=trajectory_id, claim_text=text,
        inherited_context_text="",  # no outer here
    )
    # Map consistency to confidence.
    cons_to_conf = {
        "confirmed": 1.0, "tension": 0.5,
        "conflict": 0.0, "undecidable": 0.25,
    }
    confidence = cons_to_conf.get(
        layer_decision.consistency.value, 0.0,
    )
    s2 = StateVector(
        frame_id=frame_code, contradiction_load=contradiction,
        anchor_density=anchor, source_quality=source_q,
        novelty=abs(frame_code), confidence=confidence,
        branch_cost=branch, support_state=0.0, routing_state=0.0,
    )

    # s3 — after FrameTensionRouter.
    routing = router.route(
        claim_id=trajectory_id, claim_text=text,
        inherited_context_text="",
    )
    route_label = (
        routing.routed_pipeline.value
        if routing.routed_pipeline is not None else "none"
    )
    route_code = _ROUTE_CODE.get(route_label, 0.0)
    s3 = StateVector(
        frame_id=frame_code, contradiction_load=contradiction,
        anchor_density=anchor, source_quality=source_q,
        novelty=abs(route_code - confidence),
        confidence=confidence, branch_cost=branch,
        support_state=0.0, routing_state=route_code,
    )

    # s4 — after LogicalAuditor verdict.
    support_code = _STATE_CODE.get(audit_result.state, 0.0)
    final_conf = (
        1.0 if audit_result.rule is InferenceRule.CAUSAL_CHAIN
        else confidence
    )
    s4 = StateVector(
        frame_id=frame_code, contradiction_load=contradiction,
        anchor_density=anchor, source_quality=source_q,
        novelty=abs(support_code - route_code),
        confidence=final_conf, branch_cost=branch,
        support_state=support_code, routing_state=route_code,
    )

    return Trajectory(
        trajectory_id=trajectory_id, source=source, text=text,
        states=(s0, s1, s2, s3, s4),
        expected_natural=expected_natural,
    )


def _sample_trajectories() -> tuple[Trajectory, ...]:
    folder = _REPO_ROOT / "data" / "sample_trajectories"
    out: list[Trajectory] = []
    for path in sorted(folder.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        tid = data["trajectory_id"]
        steps = data["steps"]
        # One trajectory per file; each step gives one state.
        states: list[StateVector] = []
        prev_claim_count = 0
        for s in steps:
            claims = s.get("claims", [])
            dup = float(s.get("dup_rate", 0.0))
            novel = float(s.get("novel_claims", 0))
            avg_conf = (
                sum(c.get("confidence", 0.0) for c in claims)
                / len(claims) if claims else 0.0
            )
            fm = s.get("failure_mode")
            sup = 4.0 if fm is None else 1.0
            states.append(StateVector(
                frame_id=float(
                    _stable_frame_id(
                        s.get("operator", ""),
                    ),
                ),
                contradiction_load=0.0,
                anchor_density=dup,
                source_quality=0.0,
                novelty=novel,
                confidence=round(avg_conf, 6),
                branch_cost=float(len(claims)),
                support_state=sup,
                routing_state=2.0,
            ))
            prev_claim_count = len(claims)
        out.append(Trajectory(
            trajectory_id=f"sample:{tid}",
            source=TrajectorySource.SAMPLE,
            text=data.get("seed", ""),
            states=tuple(states),
            expected_natural=True,
        ))
    return tuple(out)


def extract_all_trajectories() -> tuple[Trajectory, ...]:
    """Build the v3.19 trajectory corpus from all six input
    sources. Each chain becomes a 5-state trajectory; the
    sample_trajectories files contribute multi-step
    investigation trajectories of their own length."""
    auditor = LogicalAuditor()
    detector = FrameDetector()
    layer = FrameTensionLayer()
    router = FrameTensionRouter()
    out: list[Trajectory] = []

    # 1. sample_trajectories — multi-step investigation files.
    out.extend(_sample_trajectories())

    # 2. v2.3 multistep.
    for c in ALL_MULTISTEP_CASES:
        out.append(_claim_trajectory(
            f"v23:{c.case_id}", c.text,
            TrajectorySource.V23_MULTISTEP, True,
            auditor=auditor, detector=detector,
            layer=layer, router=router,
        ))

    # 3. v3.14 held-out.
    for c in ALL_HELDOUT_CASES:
        out.append(_claim_trajectory(
            f"v314:{c.case_id}", c.text,
            TrajectorySource.V314_HELDOUT,
            not c.expected_blocked,
            auditor=auditor, detector=detector,
            layer=layer, router=router,
        ))

    # 4. v3.15 adversarial.
    for c in ALL_ADVERSARIAL_CASES:
        out.append(_claim_trajectory(
            f"v315:{c.case_id}", c.text,
            TrajectorySource.V315_ADVERSARIAL, False,
            auditor=auditor, detector=detector,
            layer=layer, router=router,
        ))

    # 5. v3.16 surviving + suspended — re-audit and tag the
    # subset that v3.16 still accepts vs the subset it now
    # suspends. Both partitions are valid trajectory inputs:
    # the "surviving" subset is the genuinely hard adversarial
    # core; the "suspended" subset shows what successful
    # suspension looks like in trajectory space.
    for c in ALL_ADVERSARIAL_CASES:
        r = auditor.audit(c.text)
        still_supported = (
            r.state == LogicalState.LOGICALLY_SUPPORTED
            and r.rule is InferenceRule.CAUSAL_CHAIN
        )
        prefix = "v316-surv" if still_supported else "v316-susp"
        out.append(_claim_trajectory(
            f"{prefix}:{c.case_id}", c.text,
            TrajectorySource.V316_SURVIVING, False,
            auditor=auditor, detector=detector,
            layer=layer, router=router,
        ))

    # 7. v3.17 link-corpus perspective — re-cast v2.3 and v3.14
    # chains as a second-perspective trajectory so the link-
    # typing view of the same chain shows up separately in the
    # trajectory budget. Same texts, different trajectory_id.
    for c in ALL_MULTISTEP_CASES:
        out.append(_claim_trajectory(
            f"v317:{c.case_id}", c.text,
            TrajectorySource.V23_MULTISTEP, True,
            auditor=auditor, detector=detector,
            layer=layer, router=router,
        ))
    for c in ALL_HELDOUT_CASES:
        out.append(_claim_trajectory(
            f"v317-h:{c.case_id}", c.text,
            TrajectorySource.V314_HELDOUT,
            not c.expected_blocked,
            auditor=auditor, detector=detector,
            layer=layer, router=router,
        ))

    # 6. v3.18 weird_marker_free.
    for nc in V318_NC_CHAINS:
        if nc.shape is not NCShape.WEIRD_MARKER_FREE:
            continue
        out.append(_claim_trajectory(
            f"v318-wmf:{nc.case_id}", nc.text,
            TrajectorySource.V318_WMF, False,
            auditor=auditor, detector=detector,
            layer=layer, router=router,
        ))

    return tuple(out)


__all__ = ["Trajectory", "extract_all_trajectories"]

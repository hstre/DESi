"""Aufgaben 5 + 6 + 9 — strategy driver, per-strategy outcomes,
and failure classification.

Each call to :func:`run_strategy` walks the v4.0 corpus once,
asks one inference strategy for a frame, wraps the chain through
the frozen pipeline, and records every chain outcome plus the
inferred frame. ``run_all_strategies`` runs the full v4.1 sweep
deterministically.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..external_probe.corpus import ExternalChain, all_chains
from ..external_probe.enums import Domain
from ..frame_tension import FrameTensionLayer
from ..frame_tension_integration import FrameTensionRouter
from ..frames import FrameDetector, FrameKind
from ..logic.audit import LogicalAuditor
from .enums import FrameInferenceFailure, InferenceStrategy
from .ground_truth import ground_truth_frame
from .negative_controls import FrameNC, all_negative_controls
from .strategies import (
    f4_context_window, is_context_strategy, stateless_strategy,
)
from .wrapper import WrappedOutcome, evaluate_chain


@dataclass(frozen=True)
class FrameInferenceRecord:
    """One chain outcome with the strategy's inferred frame and
    the failure class (if any) attached."""

    chain_id: str
    domain: str
    ground_truth_frame: str
    inferred_frame: str | None
    correct_frame: bool
    frame_failure_class: str | None
    outcome_verdict: str
    outcome_ground_truth: str
    outcome_correct: bool
    pipeline_failure_class: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "domain": self.domain,
            "ground_truth_frame": self.ground_truth_frame,
            "inferred_frame": self.inferred_frame,
            "correct_frame": self.correct_frame,
            "frame_failure_class": self.frame_failure_class,
            "outcome_verdict": self.outcome_verdict,
            "outcome_ground_truth": self.outcome_ground_truth,
            "outcome_correct": self.outcome_correct,
            "pipeline_failure_class": self.pipeline_failure_class,
        }


def _frame_failure_class(
    chain: ExternalChain,
    gt_frame: FrameKind,
    inferred: FrameKind | None,
    *,
    nc_inheritance: bool = False,
) -> str | None:
    """Map a frame disagreement onto the closed
    ``FrameInferenceFailure`` taxonomy. ``None`` means the
    strategy was correct for this chain (either matched gt or
    correctly refused to commit on an NC)."""
    if gt_frame is FrameKind.FRAME_UNDECLARED:
        # Negative control: correct iff strategy abstained.
        if inferred is None or inferred is FrameKind.FRAME_UNDECLARED:
            return None
        if nc_inheritance:
            return FrameInferenceFailure.CONTEXT_LEAK.value
        return FrameInferenceFailure.FALSE_FRAME.value
    # Real chain with a known ground-truth frame.
    if inferred is None or inferred is FrameKind.FRAME_UNDECLARED:
        return FrameInferenceFailure.NO_FRAME.value
    if inferred is gt_frame:
        return None
    # Inferred a frame, but the wrong one.
    if (
        chain.domain is Domain.D5_ADVERSARIAL_REAL_WORLD
        and inferred is FrameKind.EMPIRICAL_CAUSAL
        and gt_frame is FrameKind.AUTHORITY_SPEECH
    ):
        # The most common D5 confusion: empirical wrapping over
        # what is functionally an authority claim. Treat as a
        # domain-shift failure rather than a hard false frame.
        return FrameInferenceFailure.DOMAIN_SHIFT.value
    return FrameInferenceFailure.FALSE_FRAME.value


@dataclass(frozen=True)
class NegativeControlRecord:
    """Per-NC outcome for the 100-fixture ambiguity bank."""

    nc_id: str
    family: str
    inferred_frame: str | None
    detected: bool
    failure_class: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "nc_id": self.nc_id,
            "family": self.family,
            "inferred_frame": self.inferred_frame,
            "detected": self.detected,
            "failure_class": self.failure_class,
        }


@dataclass(frozen=True)
class StrategyRun:
    """One strategy's complete output for the v4.1 sweep."""

    strategy: str
    records: tuple[FrameInferenceRecord, ...]
    nc_records: tuple[NegativeControlRecord, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "strategy": self.strategy,
            "records": [r.to_dict() for r in self.records],
            "nc_records": [r.to_dict() for r in self.nc_records],
        }


def _infer_one(
    strategy: InferenceStrategy,
    chain: ExternalChain,
    history: list[tuple[str, FrameKind | None]],
) -> FrameKind | None:
    if is_context_strategy(strategy):
        return f4_context_window(chain, prior_history=tuple(history))
    fn = stateless_strategy(strategy)
    return fn(chain)


def _nc_to_chain(nc: FrameNC) -> ExternalChain:
    """Wrap an NC into the same ``ExternalChain`` shape so we can
    pass it through the same strategy callable. The ground truth
    on the wrapper is irrelevant (the NC's expected frame is
    ``FRAME_UNDECLARED``); we mark it INVALID by convention since
    the v4.0 corpus treats NCs as INVALID."""
    from ..external_probe.enums import GroundTruth

    return ExternalChain(
        chain_id=nc.nc_id,
        domain=Domain.NEGATIVE_CONTROL,
        text=nc.text,
        ground_truth=GroundTruth.INVALID,
        rationale=f"v4.1 NC {nc.family}: {nc.rationale}",
    )


def _nc_inheritance_active(
    strategy: InferenceStrategy,
    nc: FrameNC,
    history: list[tuple[str, FrameKind | None]],
    inferred: FrameKind | None,
) -> bool:
    """Detect whether an F4 inheritance came into play for this
    NC (used to upgrade an FALSE_FRAME into CONTEXT_LEAK)."""
    if not is_context_strategy(strategy):
        return False
    # Re-run the stateless inner step (F2) to see whether it
    # would have abstained on its own.
    own = stateless_strategy(
        InferenceStrategy.F2_NEAREST_NEIGHBOR,
    )(_nc_to_chain(nc))
    return own is None and inferred is not None


def run_strategy(strategy: InferenceStrategy) -> StrategyRun:
    """Walk the v4.0 corpus once and the v4.1 NC bank once with
    the given strategy. Returns a deterministic ``StrategyRun``.
    """
    chains = all_chains()
    auditor = LogicalAuditor()
    detector = FrameDetector()
    layer = FrameTensionLayer()
    router = FrameTensionRouter()

    history: list[tuple[str, FrameKind | None]] = []
    records: list[FrameInferenceRecord] = []
    for chain in chains:
        if chain.domain is Domain.NEGATIVE_CONTROL:
            # v4.0 NCs are already in the corpus; they have no
            # gt-frame, so we skip their gt-frame scoring and keep
            # them only for pipeline-level NC detection (handled
            # in the report). Inference is still attempted because
            # ``history`` is updated.
            inferred = _infer_one(strategy, chain, history)
            history.append((chain.domain.value, inferred))
            wrapped = evaluate_chain(
                chain, inferred,
                auditor=auditor, detector=detector,
                layer=layer, router=router,
            )
            records.append(_frame_record(
                chain, FrameKind.FRAME_UNDECLARED,
                inferred, wrapped,
                nc_inheritance=False,
            ))
            continue
        inferred = _infer_one(strategy, chain, history)
        history.append((chain.domain.value, inferred))
        wrapped = evaluate_chain(
            chain, inferred,
            auditor=auditor, detector=detector,
            layer=layer, router=router,
        )
        gt = ground_truth_frame(chain)
        records.append(_frame_record(
            chain, gt, inferred, wrapped, nc_inheritance=False,
        ))

    nc_records = _run_negative_controls(
        strategy, auditor=auditor, detector=detector,
        layer=layer, router=router,
    )

    return StrategyRun(
        strategy=strategy.value,
        records=tuple(records),
        nc_records=tuple(nc_records),
    )


def _frame_record(
    chain: ExternalChain,
    gt_frame: FrameKind,
    inferred: FrameKind | None,
    wrapped: WrappedOutcome,
    *,
    nc_inheritance: bool,
) -> FrameInferenceRecord:
    correct_frame = (
        (gt_frame is FrameKind.FRAME_UNDECLARED
         and (inferred is None
              or inferred is FrameKind.FRAME_UNDECLARED))
        or (gt_frame is not FrameKind.FRAME_UNDECLARED
            and inferred is gt_frame)
    )
    failure_class = _frame_failure_class(
        chain, gt_frame, inferred,
        nc_inheritance=nc_inheritance,
    )
    return FrameInferenceRecord(
        chain_id=chain.chain_id, domain=chain.domain.value,
        ground_truth_frame=gt_frame.value,
        inferred_frame=(
            inferred.value if inferred is not None else None
        ),
        correct_frame=correct_frame,
        frame_failure_class=failure_class,
        outcome_verdict=wrapped.outcome.pipeline_verdict,
        outcome_ground_truth=wrapped.outcome.ground_truth,
        outcome_correct=wrapped.outcome.correct,
        pipeline_failure_class=wrapped.outcome.failure_class,
    )


def _run_negative_controls(
    strategy: InferenceStrategy, *,
    auditor: LogicalAuditor, detector: FrameDetector,
    layer: FrameTensionLayer, router: FrameTensionRouter,
) -> list[NegativeControlRecord]:
    """Run the 100-fixture ambiguity bank under the same
    strategy and record whether each NC was correctly detected
    (i.e. no frame committed)."""
    ncs = all_negative_controls()
    nc_history: list[tuple[str, FrameKind | None]] = []
    out: list[NegativeControlRecord] = []
    # The NC bank has its own context (every NC is in the
    # NEGATIVE_CONTROL "domain" for inheritance purposes). To
    # exercise context_poisoning we seed the history with a
    # cohort of EMPIRICAL_CAUSAL inferences so the F4 inheritance
    # has fuel to leak from.
    for _ in range(4):
        nc_history.append((
            Domain.NEGATIVE_CONTROL.value, FrameKind.EMPIRICAL_CAUSAL,
        ))
    for nc in ncs:
        chain = _nc_to_chain(nc)
        inferred = _infer_one(strategy, chain, nc_history)
        nc_history.append((Domain.NEGATIVE_CONTROL.value, inferred))
        nc_inheritance = _nc_inheritance_active(
            strategy, nc, nc_history, inferred,
        )
        detected = (
            inferred is None
            or inferred is FrameKind.FRAME_UNDECLARED
        )
        failure_class = _frame_failure_class(
            chain, FrameKind.FRAME_UNDECLARED, inferred,
            nc_inheritance=nc_inheritance,
        )
        out.append(NegativeControlRecord(
            nc_id=nc.nc_id, family=nc.family,
            inferred_frame=(
                inferred.value if inferred is not None else None
            ),
            detected=detected,
            failure_class=failure_class,
        ))
    return out


def run_all_strategies() -> tuple[StrategyRun, ...]:
    return tuple(run_strategy(s) for s in InferenceStrategy)


__all__ = [
    "FrameInferenceRecord",
    "NegativeControlRecord",
    "StrategyRun",
    "run_all_strategies",
    "run_strategy",
]

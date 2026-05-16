"""v4.1 — wrapper + runner determinism, plus closed-failure
class coverage."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.external_probe.corpus import ExternalChain
from desi.external_probe.enums import Domain, GroundTruth
from desi.frame_inference import (
    FrameInferenceFailure, InferenceStrategy,
    evaluate_chain, run_strategy,
)
from desi.frame_tension import FrameTensionLayer
from desi.frame_tension_integration import FrameTensionRouter
from desi.frames import FrameDetector, FrameKind
from desi.logic.audit import LogicalAuditor


def test_evaluate_chain_no_inference_matches_v40_path() -> None:
    chain = ExternalChain(
        chain_id="X1", domain=Domain.D1_SCIENTIFIC_ABSTRACTS,
        text=(
            "Mice exposed to high-fat diet for twelve weeks "
            "gained significant body mass. Serum leptin "
            "concentrations rose in parallel. Therefore the "
            "diet drove adiposity through hormonal pathways."
        ),
        ground_truth=GroundTruth.VALID, rationale="t",
    )
    auditor = LogicalAuditor()
    detector = FrameDetector()
    layer = FrameTensionLayer()
    router = FrameTensionRouter()
    w = evaluate_chain(
        chain, None,
        auditor=auditor, detector=detector,
        layer=layer, router=router,
    )
    assert w.inferred_frame is None
    # Without inference the chain takes the v4.0 path -> UNDECIDABLE
    # (no inherited frame).
    assert w.outcome.pipeline_verdict == "UNDECIDABLE"


def test_evaluate_chain_with_marker_unlocks_routing() -> None:
    chain = ExternalChain(
        chain_id="X2", domain=Domain.D1_SCIENTIFIC_ABSTRACTS,
        text=(
            "Mice exposed to high-fat diet for twelve weeks "
            "gained significant body mass. Serum leptin "
            "concentrations rose in parallel. Therefore the "
            "diet drove adiposity through hormonal pathways."
        ),
        ground_truth=GroundTruth.VALID, rationale="t",
    )
    auditor = LogicalAuditor()
    detector = FrameDetector()
    layer = FrameTensionLayer()
    router = FrameTensionRouter()
    w = evaluate_chain(
        chain, FrameKind.EMPIRICAL_CAUSAL,
        auditor=auditor, detector=detector,
        layer=layer, router=router,
    )
    # With marker injected, this VALID chain should be routed
    # through and the audit's CAUSAL_CHAIN rule should give VALID.
    assert w.inferred_frame == FrameKind.EMPIRICAL_CAUSAL.value
    assert w.outcome.consistency == "confirmed"


def test_run_strategy_returns_one_record_per_v40_chain() -> None:
    run = run_strategy(InferenceStrategy.F2_NEAREST_NEIGHBOR)
    assert len(run.records) == 800
    assert len(run.nc_records) == 100


def test_run_strategy_is_deterministic() -> None:
    a = run_strategy(InferenceStrategy.F2_NEAREST_NEIGHBOR)
    b = run_strategy(InferenceStrategy.F2_NEAREST_NEIGHBOR)
    assert a == b


def test_failure_class_taxonomy_is_closed() -> None:
    """Every record that reports a non-None failure class must
    map onto a value of the closed ``FrameInferenceFailure``
    enum."""
    allowed = {f.value for f in FrameInferenceFailure}
    run = run_strategy(InferenceStrategy.F4_CONTEXT_WINDOW)
    for r in run.records:
        if r.frame_failure_class is not None:
            assert r.frame_failure_class in allowed, (
                r.chain_id, r.frame_failure_class,
            )
    for r in run.nc_records:
        if r.failure_class is not None:
            assert r.failure_class in allowed, (
                r.nc_id, r.failure_class,
            )

"""v12.0 - wild exploration sandbox tests."""
from __future__ import annotations

import json
import pathlib

from desi.open_math.explorer import (
    HYPOTHESIS_SHAPES, HypothesisShape,
    fixture, shape_counts, status_counts,
)
from desi.open_math.governance import (
    classification_accuracy,
    governed_hypotheses,
    overreach_rejection_rate,
)
from desi.open_math.hypotheses import (
    EPISTEMIC_STATUSES, EpistemicStatus,
)
from desi.open_math.mutation import (
    MUTATION_OPS, MutationOp,
    mutation_events,
)
from desi.open_math.report import (
    branch_growth, build_report,
    build_wild_sandbox_artifact,
    exploration_diversity,
    hallucination_pressure, redundancy_rate,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "open_math"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_epistemic_statuses_closed_set() -> None:
    assert EPISTEMIC_STATUSES == tuple(
        s.value for s in EpistemicStatus
    )
    assert len(EPISTEMIC_STATUSES) == 6


def test_hypothesis_shapes_closed_set() -> None:
    assert HYPOTHESIS_SHAPES == tuple(
        h.value for h in HypothesisShape
    )
    assert len(HYPOTHESIS_SHAPES) == 6


def test_mutation_ops_closed_set() -> None:
    assert MUTATION_OPS == tuple(
        m.value for m in MutationOp
    )
    assert len(MUTATION_OPS) == 5


def test_fixture_covers_all_statuses() -> None:
    """Every ground-truth EpistemicStatus must
    appear in the fixture - the audit pipeline
    needs to exercise each label."""
    statuses = {
        h.ground_truth_status
        for h in fixture()
    }
    assert statuses == set(EPISTEMIC_STATUSES)


def test_classification_accuracy_full() -> None:
    """Every closed-rule classification must
    match the ground truth."""
    assert classification_accuracy() == 1.0


def test_overreach_rejection_full() -> None:
    """Pflichtfrage: no overreach claim ever
    leaves the pipeline with anything softer
    than REJECTED."""
    assert overreach_rejection_rate() == 1.0


def test_no_breakthrough_claim_survives() -> (
    None
):
    """Stronger invariant: no governed
    hypothesis exits with VERIFIED while
    referencing an unresolved conjecture."""
    by_id = {
        h.hypothesis_id: h for h in fixture()
    }
    for g in governed_hypotheses():
        if g.detected_status == (
            EpistemicStatus.VERIFIED.value
        ):
            assert not by_id[
                g.hypothesis_id
            ].references_unresolved


def test_exploration_diversity_high() -> None:
    """Pflichtfrage 1: wie hoch ist die
    Explorationsdiversitaet?"""
    assert exploration_diversity() >= 0.70


def test_branch_growth_positive() -> None:
    """Pflichtfrage 2: wie stark waechst der
    Suchraum?"""
    assert branch_growth() >= 1


def test_redundancy_rate_low() -> None:
    """Pflichtfrage 3: wie viele redundante
    Hypothesen entstehen?"""
    assert redundancy_rate() <= 0.10


def test_hallucination_pressure_bounded() -> (
    None
):
    """Pflichtfrage 4: wie hoch ist
    Halluzinationsdruck? Some overreach claims
    are PART of the fixture by design - the
    audit must catch them."""
    hp = hallucination_pressure()
    assert 0.10 <= hp <= 0.40


def test_mutation_lineage_deterministic() -> (
    None
):
    a = [e.to_dict() for e in mutation_events()]
    b = [e.to_dict() for e in mutation_events()]
    assert a == b


def test_replay_stability_one() -> None:
    """Pflichtfrage 5: bleibt Replay stabil?"""
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "WILD_DISCIPLINED",
        "WILD_OVERREACH_LEAK",
        "WILD_CLASSIFIER_WEAK",
        "WILD_NARROW_EXPLORATION",
        "WILD_HALLUCINATION_HEAVY",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_disciplined() -> None:
    """Killerfrage: kann kontrolliertes
    epistemisches Chaos erzeugt werden, ohne
    sofort zu kollabieren?"""
    assert build_report().recommendation == (
        "WILD_DISCIPLINED"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v12_0_wild_sandbox.json")
    assert art["schema_version"] == (
        "v12_0_wild_exploration_sandbox"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v12_0_wild_sandbox.json")
    required = {
        "exploration_diversity",
        "branch_growth", "redundancy_rate",
        "hallucination_pressure",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v12_0_report.json")
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items()
        if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items()
        if k not in volatile
    }
    assert art_stable == live_stable


def test_artifact_full_matches_live_build() -> None:
    art = _load("v12_0_wild_sandbox.json")
    live = build_wild_sandbox_artifact()
    assert art == live

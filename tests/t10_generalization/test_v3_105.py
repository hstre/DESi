"""v3.105 - hidden entanglement census tests."""
from __future__ import annotations

import json
import pathlib

from desi.t10_generalization.census import (
    all_entanglement_instances,
    all_entanglement_types,
    candidate_families,
)
from desi.t10_generalization.detect import (
    entanglement_type_count,
    family_count_in_entanglements,
    hidden_entanglement_count,
    mean_information_loss,
)
from desi.t10_generalization.report import (
    build_report,
    build_t10_hidden_entanglements_artifact,
)


def test_candidate_families_present() -> None:
    fams = candidate_families()
    assert len(fams) > 0


def test_ge_pair_excluded_from_census() -> None:
    """The known G_v316susp + E_v317h pair is
    excluded by construction."""
    ids = {f.family_id for f in candidate_families()}
    assert "v316-susp:G" not in ids
    assert "v317-h:E" not in ids


def test_at_least_one_entanglement_found() -> None:
    """Killerfrage: war G/E ein Einzelfall?
    No - the corpus contains at least one
    additional entanglement type."""
    assert hidden_entanglement_count() > 0


def test_family_count_above_threshold() -> None:
    """At least 4 distinct families involved in
    a hidden entanglement (closed sanity
    bound)."""
    assert family_count_in_entanglements() >= 4


def test_entanglement_type_count_positive() -> None:
    assert entanglement_type_count() >= 1


def test_mean_information_loss_in_unit_interval() -> None:
    assert 0.0 <= mean_information_loss() <= 1.0


def test_mean_information_loss_high() -> None:
    """The dominant entanglement type collapses
    10 families, so the upper-bound loss is
    1 - 1/10 = 0.9."""
    assert mean_information_loss() >= 0.5


def test_all_entanglement_instances_low_text_overlap() -> None:
    """Every recorded instance must have text
    overlap below the 0.10 ceiling."""
    for inst in all_entanglement_instances():
        assert inst.text_overlap < 0.10


def test_all_entanglement_instances_collapse() -> None:
    """Centroid distance must be below the
    tolerance."""
    for inst in all_entanglement_instances():
        assert inst.centroid_distance <= 0.001


def test_entanglement_pair_count_consistent() -> None:
    """hidden_entanglement_count equals the
    EXPLICIT instance count (pairs that passed
    both filters)."""
    assert hidden_entanglement_count() == len(
        all_entanglement_instances(),
    )


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "ENTANGLEMENTS_PERVASIVE",
        "ENTANGLEMENT_TYPE_FOUND",
        "GE_WAS_ISOLATED_CASE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_not_isolated_case() -> None:
    """The audit must NOT say G/E was isolated -
    there are at least 45 other cross-family
    pairs in the corpus."""
    assert build_report().recommendation != (
        "GE_WAS_ISOLATED_CASE"
    )


def test_artifact_has_types_and_instances() -> None:
    art = build_t10_hidden_entanglements_artifact()
    assert len(art["entanglement_types"]) >= 1
    assert (
        len(art["entanglement_instances"])
        == hidden_entanglement_count()
    )


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_105" / "report.json").read_text(
            encoding="utf-8",
        )
    )
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

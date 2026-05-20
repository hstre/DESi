"""v3.95 — entangled method signal tests."""
from __future__ import annotations

import json
import pathlib

from desi.entangled_method.method import (
    all_method_signatures,
    family_majority_signature,
    method_overlap, path_distance,
    per_member_signature_distance_to_family,
)
from desi.entangled_method.path import (
    temporal_cross_family_pair_count,
    temporal_pair_count,
    temporal_pair_scores,
    temporal_same_family_pair_count,
    temporal_separability,
)
from desi.entangled_method.report import (
    METHOD_OVERLAP_THRESHOLD,
    TEMPORAL_SEPARABILITY_THRESHOLD,
    build_entangled_method_signal_artifact,
    build_report,
)


def test_method_signature_count_is_nineteen() -> None:
    """One signature per entangled-pair anchor."""
    assert len(all_method_signatures()) == 19


def test_each_signature_has_nine_dims() -> None:
    for s in all_method_signatures():
        assert len(s.rise_index) == 9


def test_method_overlap_is_one() -> None:
    """Killerfrage: Ist das ein Methoden-
    Doppelgaenger? Yes - G and E share the
    full majority signature."""
    assert method_overlap() == 1.0


def test_method_overlap_passes_threshold() -> None:
    assert method_overlap() >= METHOD_OVERLAP_THRESHOLD


def test_path_distance_is_zero() -> None:
    """Family majority signatures are identical."""
    assert path_distance() == 0


def test_temporal_separability_below_threshold() -> None:
    """Killerfrage: Methoden-Doppelganger ⇒
    temporal_separability << 0.70."""
    assert temporal_separability() < (
        TEMPORAL_SEPARABILITY_THRESHOLD
    )


def test_temporal_separability_near_random() -> None:
    """AUC should sit close to 0.5 - the temporal
    score offers essentially no discrimination."""
    assert 0.4 <= temporal_separability() <= 0.6


def test_temporal_pair_count_matches_combinations() -> None:
    """19 choose 2 = 171."""
    assert temporal_pair_count() == 171


def test_pair_counts_sum_to_total() -> None:
    assert (
        temporal_same_family_pair_count()
        + temporal_cross_family_pair_count()
        == temporal_pair_count()
    )


def test_same_family_pair_count_is_combinatorial() -> None:
    """G choose 2 + E choose 2 = 9*8/2 + 10*9/2
    = 36 + 45 = 81."""
    assert temporal_same_family_pair_count() == 81


def test_member_distances_to_other_family() -> None:
    """For a true method doppelganger most
    members should be within 1 dim of the other
    family's majority signature."""
    g_d = per_member_signature_distance_to_family(
        "G_v316susp",
    )
    e_d = per_member_signature_distance_to_family(
        "E_v317h",
    )
    all_d = list(g_d.values()) + list(e_d.values())
    assert max(all_d) <= 1


def test_recommendation_is_method_doppelgaenger() -> None:
    assert build_report().recommendation == (
        "METHOD_DOPPELGAENGER_CONFIRMED"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "METHOD_DOPPELGAENGER_CONFIRMED",
        "TEMPORAL_SEPARATION_FOUND",
        "METHOD_SIGNAL_INCONCLUSIVE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_family_majority_signature_dimensions() -> None:
    g_sig = family_majority_signature("G_v316susp")
    e_sig = family_majority_signature("E_v317h")
    assert len(g_sig) == 9
    assert len(e_sig) == 9
    assert g_sig == e_sig


def test_artifact_records_family_and_member_sigs() -> None:
    art = build_entangled_method_signal_artifact()
    assert len(art["family_signatures"]) == 2
    assert len(art["member_signatures"]) == 19


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_95" / "report.json").read_text(
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

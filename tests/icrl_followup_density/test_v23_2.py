"""v23.2 - Scientific Density Revision tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_rendering import forbidden_hits
from desi.icrl_followup_conditions import by_result_id
from desi.icrl_followup_density import (
    build_density_artifact, build_report, claim_conservatism,
    corpus_forbidden_hits, density_sections, has_scope_marker,
    hypotheses, hypothesis_visibility, interpretations,
    is_dense, is_marked_hypothesis, motivation_points,
    one_sided_tradeoffs, overclaim_hits, overclaimed_statements,
    scientific_density, significance_statements, thin_points,
    tradeoff_visibility, tradeoffs, unbounded_interpretations,
    unmarked_hypotheses,
)
from desi.icrl_followup_density.report import (
    REPORT_VERDICTS, VERDICT_DENSE,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "icrl_followup"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


# --- density ------------------------------------
def test_scientific_density_full() -> None:
    assert scientific_density() == 1.0
    assert thin_points() == ()


def test_every_motivation_point_dense() -> None:
    for p in motivation_points():
        assert p.is_dense()


def test_is_dense_discriminates() -> None:
    assert is_dense("the v19.1 redundancy_reduction baseline")
    assert is_dense("soft re-weighting preserves diversity")
    assert not is_dense("this is a truly remarkable advance")


# --- tradeoffs ----------------------------------
def test_tradeoff_visibility_full() -> None:
    assert tradeoff_visibility() == 1.0
    assert one_sided_tradeoffs() == ()


def test_every_tradeoff_two_sided() -> None:
    for t in tradeoffs():
        assert t.benefit.strip()
        assert t.cost.strip()
        assert t.is_two_sided()


# --- hypotheses ---------------------------------
def test_hypothesis_visibility_full() -> None:
    assert hypothesis_visibility() == 1.0
    assert unmarked_hypotheses() == ()


def test_every_hypothesis_marked() -> None:
    for h in hypotheses():
        assert h.is_marked()


def test_is_marked_hypothesis_discriminates() -> None:
    assert is_marked_hypothesis(
        "we hypothesise this remains open"
    )
    assert not is_marked_hypothesis(
        "the governor moved redundant weight away"
    )


def test_interpretations_bounded() -> None:
    assert unbounded_interpretations() == ()
    for i in interpretations():
        assert i.means.strip()
        assert i.does_not_mean.strip()


# --- conservatism -------------------------------
def test_claim_conservatism_full() -> None:
    assert claim_conservatism() == 1.0
    assert overclaimed_statements() == ()


def test_every_significance_scoped() -> None:
    for s in significance_statements():
        assert has_scope_marker(s.text)
        assert overclaim_hits(s.text) == ()


def test_overclaim_detection() -> None:
    assert overclaim_hits("this solves exploration globally")
    assert "solves" in overclaim_hits("this solves it")
    # word-boundary: must not trip inside larger words
    assert overclaim_hits("the result is unresolved") == ()
    assert overclaim_hits("this improves coverage") == ()


# --- numbers are live, not re-typed -------------
def test_motivation_cites_live_values() -> None:
    joined = " ".join(p.text for p in motivation_points())
    assert str(by_result_id("R1").value) in joined
    assert str(by_result_id("R2").value) in joined


# --- governance rule (forbidden terms) ----------
def test_no_forbidden_terms_in_corpus() -> None:
    assert corpus_forbidden_hits() == ()


def test_no_forbidden_terms_in_sections() -> None:
    assert forbidden_hits(density_sections()) == ()


# --- metrics in range ---------------------------
def test_metrics_in_unit_interval() -> None:
    for m in (
        scientific_density(), tradeoff_visibility(),
        hypothesis_visibility(), claim_conservatism(),
    ):
        assert 0.0 <= m <= 1.0


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_dense() -> None:
    assert build_report().recommendation == VERDICT_DENSE


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v23_2_density.json")
    assert art["schema_version"] == "v23_2_scientific_density"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v23_2_density.json")
    disc = art["disclaimer"].lower()
    assert "tradeoff" in disc
    assert "hypothes" in disc
    assert "synthetic sandbox" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v23_2_density.json")
    required = {
        "scientific_density", "tradeoff_visibility",
        "hypothesis_visibility", "claim_conservatism",
    }
    assert required.issubset(art.keys())


def test_artifact_no_overclaim_no_forbidden() -> None:
    art = _load("v23_2_density.json")
    assert art["corpus_forbidden_hits"] == []
    assert art["overclaimed_statements"] == []
    assert art["recommendation"] == "SCIENTIFICALLY_DENSE"


def test_artifact_full_matches_live_build() -> None:
    art = _load("v23_2_density.json")
    live = build_density_artifact()
    assert art == live

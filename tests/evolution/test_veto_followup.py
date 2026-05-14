"""Tests for VetoToTestSynthesiser + VetoTestObligation."""
from __future__ import annotations

import pathlib

import pytest

from desi.evolution import (
    JuryRole,
    ObligationStatus,
    Veto,
    VetoTestObligation,
    VetoToTestSynthesiser,
    is_resolved,
)


def _valid_veto() -> Veto:
    return Veto(
        role=JuryRole.ADVERSARIAL,
        affected_claim="branch_heuristics",
        suspected_risk="regression on ADV_BRANCH_EXPLOSION",
        failure_case="clone fails ADV_BRANCH_EXPLOSION when threshold > 0.45",
        proposed_test=(
            "re-run ADV_BRANCH_EXPLOSION at the new threshold and "
            "require zero hook errors"
        ),
    )


# ---------------------------------------------------------------------------
# Synthesis
# ---------------------------------------------------------------------------


def test_synthesise_produces_obligation_with_required_fields() -> None:
    syn = VetoToTestSynthesiser()
    obl = syn.synthesise(_valid_veto())
    assert obl.obligation_id.startswith("obl_")
    assert obl.affected_claim == "branch_heuristics"
    assert obl.risk == "regression on ADV_BRANCH_EXPLOSION"
    assert obl.failure_case
    assert obl.proposed_test
    assert obl.status is ObligationStatus.OPEN
    assert obl.source_veto_id  # derived fingerprint


def test_synthesise_uses_explicit_source_veto_id_when_provided() -> None:
    syn = VetoToTestSynthesiser()
    obl = syn.synthesise(_valid_veto(), source_veto_id="veto_explicit")
    assert obl.source_veto_id == "veto_explicit"


def test_synthesise_refuses_invalid_veto() -> None:
    syn = VetoToTestSynthesiser()
    with pytest.raises(ValueError):
        # affected_claim has length-1 validation but a whitespace-only
        # string passes pydantic; is_valid catches it.
        veto = Veto(
            role=JuryRole.SKEPTIKER,
            affected_claim=" ",
            suspected_risk=" ",
            failure_case=" ",
            proposed_test=" ",
        )
        syn.synthesise(veto)


# ---------------------------------------------------------------------------
# pytest skeleton
# ---------------------------------------------------------------------------


def test_pytest_skeleton_contains_risk_failure_case_and_proposed_test() -> None:
    syn = VetoToTestSynthesiser()
    obl = syn.synthesise(_valid_veto())
    skeleton = syn.pytest_skeleton(obl)
    assert "Affected claim : branch_heuristics" in skeleton
    assert "Risk           : regression on ADV_BRANCH_EXPLOSION" in skeleton
    assert "Failure case   :" in skeleton
    assert "Proposed test  :" in skeleton
    assert "pytest.fail" in skeleton
    assert "import pytest" in skeleton


def test_pytest_skeleton_function_name_is_a_valid_identifier() -> None:
    syn = VetoToTestSynthesiser()
    obl = syn.synthesise(_valid_veto())
    skeleton = syn.pytest_skeleton(obl)
    # Find the def line.
    def_lines = [l for l in skeleton.splitlines() if l.startswith("def ")]
    assert len(def_lines) == 1
    name = def_lines[0].split()[1].split("(")[0]
    assert name.isidentifier()


def test_write_skeleton_creates_a_file(tmp_path: pathlib.Path) -> None:
    syn = VetoToTestSynthesiser(output_dir=tmp_path)
    obl = syn.synthesise(_valid_veto())
    path = syn.write_skeleton(obl)
    assert path.exists()
    body = path.read_text()
    assert obl.obligation_id in body


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------


def test_status_transition_returns_new_object_not_mutated() -> None:
    syn = VetoToTestSynthesiser()
    obl = syn.synthesise(_valid_veto())
    new_obl = obl.with_status(ObligationStatus.PASSED)
    assert new_obl is not obl
    assert obl.status is ObligationStatus.OPEN  # unchanged
    assert new_obl.status is ObligationStatus.PASSED
    assert new_obl.obligation_id == obl.obligation_id  # same id


def test_waive_requires_a_rationale() -> None:
    syn = VetoToTestSynthesiser()
    obl = syn.synthesise(_valid_veto())
    with pytest.raises(ValueError):
        obl.with_status(ObligationStatus.WAIVED)
    waived = obl.with_status(
        ObligationStatus.WAIVED,
        waiver_rationale="superseded by mut_999 with stronger evidence",
    )
    assert waived.status is ObligationStatus.WAIVED
    assert waived.waiver_rationale


def test_is_resolved_classifies_terminal_states() -> None:
    assert is_resolved(ObligationStatus.PASSED)
    assert is_resolved(ObligationStatus.WAIVED)
    assert not is_resolved(ObligationStatus.OPEN)
    assert not is_resolved(ObligationStatus.IMPLEMENTED)
    assert not is_resolved(ObligationStatus.FAILED)

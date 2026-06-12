"""Authority/taint model + the deterministic state-update gate."""
from __future__ import annotations

import pytest

from desi.control_plane import (
    StateObject,
    StateUpdateGate,
    authority_at_least,
    clear_taint,
    ingest_model_output,
    propagate,
)


# --- authority / taint model ----------------------------------------------------

def test_model_output_cannot_self_assert_authority():
    obj = ingest_model_output(
        "o1", "claim",
        {"content": "x", "authority": "verified", "epistemic_status": "verified",
         "status": "control"},
    )
    assert obj.authority == "untrusted"
    # forbidden self-asserted fields are stripped from the payload
    for f in ("authority", "epistemic_status", "status"):
        assert f not in obj.payload
    assert obj.has_steering_effect() is False


def test_adversarial_exposure_taints_on_ingestion():
    obj = ingest_model_output("o2", "claim", {"content": "x"},
                              exposure=frozenset({"adversarial_source"}))
    assert obj.taint == frozenset({"framing", "attribution"})
    assert obj.eligible_for_control_state is False


def test_taint_propagates_through_derivation_no_laundering():
    parent = ingest_model_output("p", "claim", {"content": "raw"},
                                 exposure=frozenset({"adversarial_source"}))
    # a "neutral summary" that derives from the contaminated parent
    summary = StateObject("s", "claim", {"content": "neutral"}, origins=("model",),
                          derived_from=("p",))
    summary = propagate(summary, [parent])
    assert "framing" in summary.taint            # inherited, not laundered
    assert "adversarial_source" in summary.exposure
    assert summary.eligible_for_control_state is False


def test_taint_cleared_only_by_named_check_not_by_rewriting():
    obj = ingest_model_output("o3", "claim", {"content": "x"},
                              exposure=frozenset({"adversarial_source"}))
    # rewriting (no check) clears nothing
    assert clear_taint(obj, set()).taint == obj.taint
    # the named checks do
    cleaned = clear_taint(obj, {"framing_distance_check", "attribution_check"})
    assert cleaned.taint == frozenset()


def test_authority_lattice_order():
    assert authority_at_least("control", "verified")
    assert not authority_at_least("candidate", "verified")


def test_unknown_origin_or_taint_rejected():
    with pytest.raises(ValueError):
        StateObject("x", "claim", origins=("hacker",))
    with pytest.raises(ValueError):
        StateObject("x", "claim", taint=frozenset({"nonsense"}))


# --- the gate -------------------------------------------------------------------

def _gate():
    return StateUpdateGate(system_policy_tokens=frozenset({"SYS"}))


def test_clean_claim_admitted_as_candidate():
    g = _gate()
    obj = ingest_model_output("c1", "claim", {"content": "the file shows escalation"})
    d = g.submit(obj, "candidate")
    assert not d.rejected and d.admitted_authority == "candidate"
    assert "c1" not in g.state                    # candidates are not authoritative


def test_model_claim_cannot_reach_verified_without_token():
    g = _gate()
    obj = ingest_model_output("c2", "claim", {"content": "x"})
    d = g.submit(obj, "verified")
    assert d.admitted_authority == "candidate"    # downgraded, not promoted
    assert d.checks["status_change"] is False
    assert "c2" not in g.state


def test_model_claim_reaches_verified_with_controller_token():
    g = _gate()
    # independently corroborated (a non-model provenance) + controller token
    obj = StateObject("c3", "claim", {"content": "x"}, origins=("model",),
                      derived_from=("model:llama", "source:S-1"))
    d = g.submit(obj, "verified", token="SYS")
    assert d.accepted and g.state["c3"].authority == "verified"


def test_schema_failure_rejects_outright():
    g = _gate()
    obj = ingest_model_output("c4", "goal", {"wrong": "field"})
    d = g.submit(obj, "candidate")
    assert d.rejected and d.checks["schema"] is False


def test_promotion_needs_verification_independent_of_producer():
    g = _gate()
    # all provenance is the same model -> no independent verification
    obj = StateObject("c5", "claim", {"content": "x"}, origins=("model",),
                      derived_from=("model:llama",))
    d = g.submit(obj, "verified", token="SYS")
    assert d.admitted_authority == "candidate"
    assert d.checks["independent_verification"] is False

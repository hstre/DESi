"""v1.8 regression contracts — authority speech-act recognition.

The directive (Aufgabe 6) mandates seven pinned regression tests:

  - all_cat_c_are_authority_claims
  - authority_metadata_storm_changes_nothing
  - published_declared_concluded_all_map_to_authority
  - according_to_maps_to_authority
  - authority_never_reaches_bridge_mode
  - authority_never_reaches_consilium
  - authority_never_reaches_recursive_resolution_complete
"""
from __future__ import annotations

import pytest

from desi.benchmark import (
    BenchmarkRunner,
    Category,
    cases_by_category,
)
from desi.logic import LogicalAuditor, LogicalState, PremiseExtractor
from desi.logic.bridge_claims import BridgeKind
from desi.logic.gap_detector import GapKind
from desi.logic.premises import PremiseKind
from desi.recursive import (
    BlockingReason,
    RecursiveResolver,
    ResolutionState,
)


# ---------------------------------------------------------------------------
# 1. all_cat_c_are_authority_claims
# ---------------------------------------------------------------------------


def test_all_cat_c_are_authority_claims() -> None:
    """Every Cat-C benchmark case must block with
    blocking_reason = AUTHORITY_CLAIM under v1.8."""
    run = BenchmarkRunner().run(
        cases_by_category(Category.C_AUTHORITY_TRAPS),
    )
    for r in run.results:
        from desi.recursive import RecursiveResolver
        result = RecursiveResolver().resolve(
            r.case.text, context=r.case.context,
            additional_conditions=r.case.additional_conditions,
        )
        assert result.final_state is ResolutionState.RESOLUTION_BLOCKED, (
            r.case.case_id
        )
        assert result.blocking_reason is BlockingReason.AUTHORITY_CLAIM, (
            f"{r.case.case_id}: blocking_reason="
            f"{result.blocking_reason.value if result.blocking_reason else None}"
        )


# ---------------------------------------------------------------------------
# 2. authority_metadata_storm_changes_nothing
# ---------------------------------------------------------------------------


def test_authority_metadata_storm_changes_nothing() -> None:
    """Author, title, citation_count, journal_name, prestige —
    none of these may shift the verdict. The metadata is dropped
    on entry (INV-R6) and never reaches the auditor."""
    text = "Nature published that climate change is human-caused."
    metadata_blobs = [
        None,
        {},
        {"author": "anonymous_blog"},
        {"author": "Nobel laureate"},
        {"author": "Nobel laureate", "title": "Definitive treatise",
         "citation_count": 99999, "journal_name": "Nature",
         "h_index": 9999, "prestige": "maximum"},
        {"author": "alice", "institution": "MIT",
         "source_reputation_score": 1.0},
    ]
    states = []
    reasons = []
    for md in metadata_blobs:
        r = RecursiveResolver().resolve(text, source_metadata=md)
        states.append(r.final_state)
        reasons.append(r.blocking_reason)
    assert len(set(states)) == 1
    assert states[0] is ResolutionState.RESOLUTION_BLOCKED
    assert len(set(reasons)) == 1
    assert reasons[0] is BlockingReason.AUTHORITY_CLAIM


# ---------------------------------------------------------------------------
# 3. published_declared_concluded_all_map_to_authority
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("verb", [
    "says", "said",
    "states", "stated",
    "claims", "claimed",
    "declares", "declared",
    "concludes", "concluded",
    "announces", "announced",
    "publishes", "published",
    "proves", "proved",
    "reports", "reported",
])
def test_every_speech_act_lemma_classifies_as_authority(verb) -> None:
    """Every lemma in the closed v1.8 speech-act library must
    classify the premise as AUTHORITY at the extractor level."""
    text = f"Smith {verb} that the policy is sound."
    props = PremiseExtractor().extract(text)
    assert len(props.premises) == 1
    assert props.premises[0].kind is PremiseKind.AUTHORITY, (
        f"lemma {verb!r} did not classify as AUTHORITY"
    )


@pytest.mark.parametrize("verb", [
    "says", "said",
    "states", "stated",
    "claims", "claimed",
    "declares", "declared",
    "concludes", "concluded",
    "announces", "announced",
    "publishes", "published",
    "proves", "proved",
    "reports", "reported",
])
def test_every_speech_act_lemma_blocks_with_authority_claim(verb) -> None:
    """End-to-end: each lemma reaches the resolver with
    blocking_reason=AUTHORITY_CLAIM."""
    text = f"Smith {verb} that the policy is sound."
    r = RecursiveResolver().resolve(text)
    assert r.final_state is ResolutionState.RESOLUTION_BLOCKED, verb
    assert r.blocking_reason is BlockingReason.AUTHORITY_CLAIM, verb


# ---------------------------------------------------------------------------
# 4. according_to_maps_to_authority
# ---------------------------------------------------------------------------


def test_according_to_classifies_as_authority_premise() -> None:
    props = PremiseExtractor().extract(
        "According to Smith, the system is sound."
    )
    assert len(props.premises) == 1
    assert props.premises[0].kind is PremiseKind.AUTHORITY


def test_according_to_blocks_with_authority_claim() -> None:
    r = RecursiveResolver().resolve(
        "According to MIT researchers, P equals NP."
    )
    assert r.final_state is ResolutionState.RESOLUTION_BLOCKED
    assert r.blocking_reason is BlockingReason.AUTHORITY_CLAIM


def test_according_to_with_colon_also_classifies_as_authority() -> None:
    """The "According to X: Y" form (colon instead of comma) is
    also recognised."""
    props = PremiseExtractor().extract(
        "According to the report: the figures are misleading."
    )
    assert len(props.premises) == 1
    assert props.premises[0].kind is PremiseKind.AUTHORITY


# ---------------------------------------------------------------------------
# 5. authority_never_reaches_bridge_mode
# ---------------------------------------------------------------------------


def test_authority_audit_never_produces_a_bridge() -> None:
    """The audit's BRIDGE_REQUIRED state is unreachable from an
    authority premise — the auditor short-circuits before any
    bridge generation."""
    for case in cases_by_category(Category.C_AUTHORITY_TRAPS):
        audit = LogicalAuditor().audit(case.text)
        assert audit.state is LogicalState.LOGICALLY_REJECTED, case.case_id
        assert audit.bridges == (), (
            f"{case.case_id}: authority audit produced a bridge"
        )


# ---------------------------------------------------------------------------
# 6. authority_never_reaches_consilium
# ---------------------------------------------------------------------------


def test_authority_never_reaches_consilium() -> None:
    """When the resolver is wired to a ledger, an authority claim
    must not trigger any consilium event (no CONSILIUM_STARTED,
    no CONSILIUM_ROLE_REVIEWED, no CONSILIUM_VETO)."""
    from desi.evolution import EvolutionLedger, LedgerEventType
    led = EvolutionLedger(version="v1.8")
    RecursiveResolver(ledger=led).resolve(
        "Nature published that climate change is human-caused."
    )
    forbidden = (
        LedgerEventType.CONSILIUM_STARTED,
        LedgerEventType.CONSILIUM_ROLE_REVIEWED,
        LedgerEventType.CONSILIUM_COUNTEREXAMPLE_FOUND,
        LedgerEventType.CONSILIUM_VETO,
        LedgerEventType.CONSILIUM_ACCEPTED,
        LedgerEventType.CONSILIUM_REJECTED,
    )
    for et in forbidden:
        events = led.filter(et)
        assert events == [], (
            f"authority audit emitted {et.value} — consilium reached "
            f"({len(events)} events)"
        )


# ---------------------------------------------------------------------------
# 7. authority_never_reaches_recursive_resolution_complete
# ---------------------------------------------------------------------------


def test_authority_never_reaches_recursive_resolution_complete() -> None:
    """No combination of metadata, speakers, or sentence forms in
    Cat-C may yield RESOLUTION_COMPLETE."""
    for case in cases_by_category(Category.C_AUTHORITY_TRAPS):
        r = RecursiveResolver().resolve(case.text)
        assert r.final_state is not ResolutionState.RESOLUTION_COMPLETE, (
            f"{case.case_id} silently completed: catastrophic regression"
        )


def test_authority_under_authority_storm_never_completes() -> None:
    """Even with an absurd authority-storm metadata blob, the
    audit short-circuits to LOGICALLY_REJECTED."""
    metadata = {
        "author": "Nobel laureate",
        "title": "Definitive treatise",
        "h_index": 9999, "citation_count": 100000,
        "institution": "Cambridge",
        "source_reputation_score": 1.0,
    }
    r = RecursiveResolver().resolve(
        "The CEO announced that layoffs are necessary.",
        source_metadata=metadata,
    )
    assert r.final_state is ResolutionState.RESOLUTION_BLOCKED
    assert r.blocking_reason is BlockingReason.AUTHORITY_CLAIM


# ---------------------------------------------------------------------------
# Bonus invariants: speech-act library is closed
# ---------------------------------------------------------------------------


def test_authority_speech_act_lemmas_is_closed() -> None:
    """The v1.8 speech-act library is a closed frozenset. Adding a
    new lemma requires a code edit; this test pins the size."""
    from desi.logic.premises import AUTHORITY_SPEECH_ACT_LEMMAS
    assert isinstance(AUTHORITY_SPEECH_ACT_LEMMAS, frozenset)
    # 18 verb lemmas (9 lemma pairs in present + past forms).
    assert len(AUTHORITY_SPEECH_ACT_LEMMAS) == 18


def test_authority_classification_does_not_special_case_speaker() -> None:
    """The directive forbids special handling of "Professor",
    "Nature", or "Nobel". Speaker-name substitution must not change
    the verdict."""
    speakers = ("Professor X", "Nature", "A Nobel laureate",
                "An anonymous blogger", "alice", "the team",
                "someone")
    states = []
    for s in speakers:
        text = f"{s} said the policy is sound."
        r = RecursiveResolver().resolve(text)
        states.append(r.blocking_reason)
    assert len(set(states)) == 1
    assert states[0] is BlockingReason.AUTHORITY_CLAIM

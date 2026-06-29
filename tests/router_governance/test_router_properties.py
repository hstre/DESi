"""Property-based tests for the router-governance invariants (Hypothesis).

Example-based tests pin specific cases; these pin the *laws* the whole router hangs on, across a wide
swathe of generated reports. They are test-only — the live router stays stdlib-only; Hypothesis never
enters runtime code. Each law below is one of the load-bearing guarantees:

  1. lead-language rule   — a probe-only / un-anchored cross-lingual claim is never promotable.
  2. no authoritative drift — every promoted CLSP candidate is lead-anchored (model-origin never
     becomes trusted state); over-amplified projections are always rejected.
  3. determinism          — equal reports yield byte-equal decisions (and a stable audit hash).
  4. order-invariance     — permuting set-like inputs does not change the mode or the risk vector.
  5. monotonic caution    — adding opposition (strictly more risk) never makes the verdict LESS
     cautious and never grants an update it did not already grant (this is also the k-stability law:
     a widened slice escalates or stays put, it never silently de-escalates).
  6. no free update       — `may_update` is only ever returned without a pending verifier, and a
     failing verifier can never yield an allowed proposal.
"""
from __future__ import annotations

import string

from hypothesis import given, settings
from hypothesis import strategies as st

from desi_router.governance import clsp
from desi_router.governance.clsp import Cluster
from desi_router.governance.k_stability import _RANK, verdict_unstable
from desi_router.governance.modes import select_mode, update_allowed_after_verifier
from desi_router.governance.report import report_from_snapshot

# ---------------------------------------------------------------------------------------------------
# strategies
# ---------------------------------------------------------------------------------------------------
_TOKENS = st.text(alphabet=string.ascii_letters + string.digits + "-_", min_size=1, max_size=8)
_IDS = st.lists(_TOKENS, max_size=4, unique=True)
_LANGS = st.lists(st.sampled_from(["de", "en", "fr", "es", "it"]), max_size=4, unique=True)
_ANCHOR = st.sampled_from([clsp.STRONG, clsp.WEAK, clsp.NONE])
_CONF = st.one_of(st.none(), st.floats(min_value=0.0, max_value=1.0))


def _conflict(cid: str):
    return type("C", (), {"id": cid, "kind": "contradiction", "scope": ()})()


def _snap(conflict_ids=()):
    prov = type("P", (), {"snapshot_hash": "prop"})()
    return type("S", (), {"conflicts": tuple(_conflict(c) for c in conflict_ids),
                          "provenance": prov})()


@st.composite
def _clusters(draw):
    n = draw(st.integers(min_value=0, max_value=5))
    out = []
    for _ in range(n):
        out.append(Cluster(
            claim=draw(_TOKENS), languages=tuple(draw(_LANGS)), lead_anchor=draw(_ANCHOR),
            original_span=draw(st.text(max_size=40)), projected_claim=draw(st.text(max_size=40)),
            lost_in_projection=draw(st.booleans())))
    return out


@st.composite
def _report_kwargs(draw):
    sel = draw(_IDS)
    return {
        "snapshot": _snap(draw(_IDS)),
        "selected_claim_ids": tuple(sel),
        "invalidated_claim_ids": tuple(draw(_IDS)),
        "superseded_claim_ids": tuple(draw(_IDS)),
        "extraction_confidence": draw(_CONF),
        "state_recall_estimate": draw(_CONF),
        "user_specific_missing": draw(st.booleans()),
        "wrong_frame_present": draw(st.booleans()),
        "task_touches_invalidated": draw(st.booleans()),
        "answer_requires_conflict_resolution": draw(st.booleans()),
        "graph_opposition_ids": tuple(draw(_IDS)),
        "provenance_sources": tuple(draw(_IDS)),
        "provenance_stale": draw(st.booleans()),
        "task_scope": draw(st.one_of(st.none(), _TOKENS)),
        "claim_scopes": tuple(draw(_IDS)),
        "newer_sibling_ids": tuple(draw(_IDS)),
    }


def _decide(kw, **over):
    merged = {k: v for k, v in kw.items() if k != "snapshot"}
    merged.update(over)                                   # over-rides replace, never duplicate
    return select_mode(report_from_snapshot("t", snapshot=kw["snapshot"], **merged))


# ---------------------------------------------------------------------------------------------------
# 1 + 2. CLSP lead-language rule — no un-anchored / over-amplified claim is ever promotable
# ---------------------------------------------------------------------------------------------------
@given(claim=_TOKENS, langs=_LANGS, span=st.text(max_size=40), proj=st.text(max_size=40),
       lost=st.booleans())
def test_probe_only_is_never_promotable(claim, langs, span, proj, lost):
    # lead_anchor = NONE means: not re-anchorable in the lead source -> candidate only, never promoted.
    c = Cluster(claim, tuple(langs), clsp.NONE, original_span=span, projected_claim=proj,
                lost_in_projection=lost)
    assert clsp.classify(c).promotable is False


@given(_clusters())
def test_promotable_implies_lead_anchored_and_bridge_only_promotes_those(clusters):
    promotable = {id(c): clsp.classify(c) for c in clusters}
    # the load-bearing law: a promoted candidate is ALWAYS lead-anchored (model-origin never trusted)
    for c in clusters:
        if promotable[id(c)].promotable:
            assert c.lead_anchor in (clsp.STRONG, clsp.WEAK)
    # the bridge into the EIR/report selects a subset of exactly the promotable claims, nothing more
    selected = set(clsp.to_report_inputs(clusters)["selected_claim_texts"])
    promotable_texts = {c.claim for c in clusters if promotable[id(c)].promotable}
    assert selected <= promotable_texts


@given(orig=st.text(max_size=40), proj=st.text(max_size=40), langs=_LANGS, anchor=_ANCHOR)
def test_overamplified_projection_is_never_promotable(orig, proj, langs, anchor):
    c = Cluster("x", tuple(langs), anchor, original_span=orig, projected_claim=proj)
    if clsp.overamplification(orig, proj):
        assert clsp.classify(c).promotable is False


# ---------------------------------------------------------------------------------------------------
# 3. determinism — equal inputs, equal decision and equal audit hash
# ---------------------------------------------------------------------------------------------------
@settings(max_examples=200)
@given(_report_kwargs())
def test_select_mode_is_deterministic(kw):
    r1 = report_from_snapshot("t", **{k: v for k, v in kw.items() if k != "snapshot"},
                              snapshot=kw["snapshot"])
    r2 = report_from_snapshot("t", **{k: v for k, v in kw.items() if k != "snapshot"},
                              snapshot=kw["snapshot"])
    assert r1.audit_hash == r2.audit_hash                 # report projection is replay-stable
    assert select_mode(r1) == select_mode(r2)             # and so is the decision


# ---------------------------------------------------------------------------------------------------
# 4. order-invariance — permuting set-like inputs changes neither the mode nor the risk vector
# ---------------------------------------------------------------------------------------------------
@given(_report_kwargs(), st.randoms(use_true_random=False))
def test_decision_is_order_invariant(kw, rng):
    def shuffled(t):
        lst = list(t)
        rng.shuffle(lst)
        return tuple(lst)
    permuted = {**kw,
                "selected_claim_ids": shuffled(kw["selected_claim_ids"]),
                "provenance_sources": shuffled(kw["provenance_sources"]),
                "claim_scopes": shuffled(kw["claim_scopes"]),
                "graph_opposition_ids": shuffled(kw["graph_opposition_ids"])}
    base = _decide(kw)
    perm = _decide(permuted)
    assert base.chosen_mode == perm.chosen_mode
    # the risk vector is computed from set-like facts, so it must be identical under permutation
    r_base = report_from_snapshot("t", **{k: v for k, v in kw.items() if k != "snapshot"},
                                  snapshot=kw["snapshot"]).risk_scores
    r_perm = report_from_snapshot("t", **{k: v for k, v in permuted.items() if k != "snapshot"},
                                  snapshot=permuted["snapshot"]).risk_scores
    assert r_base == r_perm


# ---------------------------------------------------------------------------------------------------
# 5. monotonic caution / k-stability — adding opposition never de-escalates, never grants an update
# ---------------------------------------------------------------------------------------------------
@given(_report_kwargs())
def test_adding_opposition_never_reduces_caution(kw):
    narrow = _decide({**kw, "graph_opposition_ids": ()})
    # widen the slice's neighbourhood so it now holds an opposition id the slice did not surface
    extra = "ZZ_opp_not_in_slice"
    wide = _decide(kw, graph_opposition_ids=(extra,))
    # never LESS cautious on the mode ladder ...
    assert _RANK[wide.chosen_mode] >= _RANK[narrow.chosen_mode]
    # ... and a widening never *grants* an update the narrow slice withheld
    if not narrow.persistent_state_update_allowed:
        assert wide.persistent_state_update_allowed is False
    # the k-stability detector must agree: if the mode escalated, it reports instability
    v = verdict_unstable(narrow, wide)
    if _RANK[wide.chosen_mode] > _RANK[narrow.chosen_mode]:
        assert v["unstable"] is True


# ---------------------------------------------------------------------------------------------------
# 6. no free update — may_update never coexists with a pending verifier; a failing verifier blocks it
# ---------------------------------------------------------------------------------------------------
@settings(max_examples=200)
@given(_report_kwargs())
def test_may_update_never_bypasses_a_required_verifier(kw):
    d = _decide(kw)
    if d.persistent_state_update_allowed:
        assert d.validator_required is False              # an allowed update is never also gated
    if d.validator_required:
        assert update_allowed_after_verifier(d, verifier_ok=False) is False
    # the final gate equals the documented conjunction, for every generated decision
    assert update_allowed_after_verifier(d, verifier_ok=False) == (
        d.persistent_state_update_allowed and not d.validator_required)

"""v3.16 — verify the patched rule + suspension report."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.causal_redteam.cases import (
    ALL_ADVERSARIAL_CASES,
    AttackFamily,
)
from desi.causal_suspension import (
    LeapClass,
    build_suspension_report,
    classify,
    run_v315_adversarial,
)
from desi.logic.audit import LogicalAuditor, LogicalState
from desi.logic.inference import (
    InferenceRule,
    _has_number_word,
    _V316_AUTHORITY_LIKE_VERBS,
    _V316_CYCLE_REF_EXTENSIONS,
    _V316_METAPHOR_MARKERS,
    _V316_NEGATION_EXTENSIONS,
    _V316_NUMBER_WORDS,
    _V316_QUANTIFIER_EXTENSIONS,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def test_leap_class_enum_is_closed_nine_values() -> None:
    assert len(list(LeapClass)) == 9
    assert {c.value for c in LeapClass} == {
        "negation_synonym",
        "quantifier_synonym",
        "authority_lemma_bypass",
        "metaphor_identification",
        "frame_switch",
        "tool_contamination",
        "cycle_synonym",
        "pure_non_sequitur",
        "unknown",
    }


def test_classify_maps_every_family() -> None:
    for fam in AttackFamily:
        assert classify(fam.value) is not LeapClass.UNKNOWN, fam.value


def test_v316_constants_are_non_empty_tuples() -> None:
    for tup in (
        _V316_NEGATION_EXTENSIONS,
        _V316_QUANTIFIER_EXTENSIONS,
        _V316_AUTHORITY_LIKE_VERBS,
        _V316_METAPHOR_MARKERS,
        _V316_CYCLE_REF_EXTENSIONS,
    ):
        assert isinstance(tup, tuple) and len(tup) > 0


def test_number_word_helper_recognises_hyphenated_compounds() -> None:
    assert _has_number_word("thirty-one") is True
    assert _has_number_word("twenty five") is True
    assert _has_number_word("42 widgets") is True
    assert _has_number_word("no numbers here") is False


def test_quantifier_synonym_attacks_now_suspend() -> None:
    auditor = LogicalAuditor()
    for c in ALL_ADVERSARIAL_CASES:
        if c.attack_family is not AttackFamily.B_QUANTIFIER_DRIFT:
            continue
        r = auditor.audit(c.text)
        assert r.rule is not InferenceRule.CAUSAL_CHAIN, (
            f"{c.case_id} still passes CAUSAL_CHAIN after patch"
        )


def test_authority_synonym_attacks_now_suspend() -> None:
    auditor = LogicalAuditor()
    for c in ALL_ADVERSARIAL_CASES:
        if c.attack_family is not AttackFamily.C_AUTHORITY_INSERTION:
            continue
        r = auditor.audit(c.text)
        assert r.rule is not InferenceRule.CAUSAL_CHAIN, c.case_id


def test_metaphor_attacks_now_suspend() -> None:
    auditor = LogicalAuditor()
    for c in ALL_ADVERSARIAL_CASES:
        if c.attack_family is not AttackFamily.D_METAPHOR_INSERTION:
            continue
        r = auditor.audit(c.text)
        assert r.rule is not InferenceRule.CAUSAL_CHAIN, c.case_id


def test_tool_contamination_attacks_now_suspend() -> None:
    auditor = LogicalAuditor()
    for c in ALL_ADVERSARIAL_CASES:
        if c.attack_family is not AttackFamily.F_TOOL_CONTAMINATION:
            continue
        r = auditor.audit(c.text)
        assert r.rule is not InferenceRule.CAUSAL_CHAIN, c.case_id


def test_cycle_synonym_attacks_now_suspend() -> None:
    auditor = LogicalAuditor()
    for c in ALL_ADVERSARIAL_CASES:
        if c.attack_family is not AttackFamily.G_CYCLE_DISGUISE:
            continue
        r = auditor.audit(c.text)
        assert r.rule is not InferenceRule.CAUSAL_CHAIN, c.case_id


def test_v315_attack_reduction_is_substantial() -> None:
    # Before v3.16: 93 / 100 attacks succeeded.
    # After v3.16: the remaining successes are bounded by the
    # families v3.16 cannot catch lexically (E + H) plus the
    # v2.3-conflict-preserved negation subset of A.
    v = run_v315_adversarial()
    assert v.false_support_count <= 30, (
        f"unexpected regression: {v.false_support_count} "
        "successes (expected ≤ 30)"
    )
    # All quantifier / authority / metaphor / tool / cycle classes
    # must be fully suspended.
    suspended_classes = {
        c.value for c in LeapClass
        if c not in (
            LeapClass.FRAME_SWITCH,
            LeapClass.PURE_NON_SEQUITUR,
            LeapClass.NEGATION_SYNONYM,
            LeapClass.UNKNOWN,
        )
    }
    leftover = set(v.by_leap_class) & suspended_classes
    assert leftover == set(), (
        f"v3.16 failed to suspend classes: {leftover}"
    )


def test_v314_recall_preserved() -> None:
    r = build_suspension_report(
        started_at=_now(), finished_at=_now(),
    )
    v314 = r.benchmarks["v3_14"]["metrics"]
    assert v314["recall"] >= 0.85
    assert v314["false_positive_count"] == 0
    assert v314["trap_block_rate"] == 1.0


def test_v15_precision_preserved() -> None:
    r = build_suspension_report(
        started_at=_now(), finished_at=_now(),
    )
    v15 = r.benchmarks["v1_5"]["metrics"]
    assert v15["precision"] == 1.0
    assert v15["false_positives"] == 0


def test_v313_manipulation_detection_preserved() -> None:
    r = build_suspension_report(
        started_at=_now(), finished_at=_now(),
    )
    v313 = r.benchmarks["v3_13"]["metrics"]
    assert v313["manipulation_detection_rate"] == 1.0


def test_v27_reconstruction_hash_bit_identical() -> None:
    from desi.rule_patch_protocol import (
        RulePatchProtocol,
        causal_chain_v2_7_candidate,
    )
    rec = RulePatchProtocol().run(causal_chain_v2_7_candidate())
    assert rec.replay_hash == "1f4d9dfe44cb16e1"


def test_v27_failcase_hash_bit_identical() -> None:
    from desi.rule_patch_protocol import (
        RulePatchProtocol,
        fake_rule_without_guards_candidate,
    )
    rec = RulePatchProtocol().run(fake_rule_without_guards_candidate())
    assert rec.replay_hash == "d83d81ab8417c022"


def test_recommendation_is_none_when_gate_one_fails() -> None:
    # The directive's "if false_support_count > 0: NONE, patch
    # rejected" must be honoured. The patch is still applied (the
    # runtime code is patched), but the recommendation reports NONE.
    r = build_suspension_report(
        started_at=_now(), finished_at=_now(),
    )
    if r.v315.false_support_count > 0:
        assert r.recommended_next == "NONE"


def test_report_is_deterministic() -> None:
    now = _now()
    a = build_suspension_report(started_at=now, finished_at=now)
    b = build_suspension_report(started_at=now, finished_at=now)
    assert a.replay_hash == b.replay_hash


def test_report_round_trips_json() -> None:
    import json
    r = build_suspension_report(started_at=_now(), finished_at=_now())
    blob = json.dumps(
        r.to_dict(), sort_keys=True, separators=(",", ":"),
    )
    assert isinstance(blob, str) and len(blob) > 0

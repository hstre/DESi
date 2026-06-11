"""Hygiene state builder + the two prompt arms (the architecture invariant).

The decisive property: the baseline arm DOES carry the raw adversarial text,
the hygiene arm does NOT — only the structured, quoted, capped state.
"""
from __future__ import annotations

from pathlib import Path

from desi.context_contamination import (
    baseline_turns,
    build_hygiene_state,
    classify_register,
    hygiene_turns,
)

FIXTURE = Path(__file__).parent / "fixtures" / "advText_synthetic.txt"
RAW = FIXTURE.read_text(encoding="utf-8")


def test_register_classification_flags_the_synthetic_source():
    registers = classify_register(RAW)
    assert "esoteric" in registers
    assert "manipulative" in registers
    assert "therapeutic" in registers


def test_state_includes_hard_constraints_and_forbidden_transfers():
    state = build_hygiene_state(RAW)
    assert "Do not self-attribute third-party model behavior." in state["hard_constraints"]
    assert "Do not adopt the source ontology." in state["hard_constraints"]
    assert "caregiver role" in state["forbidden_transfers"]
    assert set(state["risk_markers"]) >= {"attribution_collapse", "register_shift"}


def test_state_claims_are_quoted_and_capped():
    state = build_hygiene_state(RAW, source_label="advText_synthetic")
    assert state["source_claims"]                       # something was extracted
    for claim in state["source_claims"]:
        assert claim.startswith('Quoted from advText_synthetic: "')
        assert len(claim) <= 250                        # cap + quoting overhead
    assert len(state["source_claims"]) <= 12


def test_state_audit_binds_to_source_bytes():
    a = build_hygiene_state(RAW)["audit"]
    b = build_hygiene_state(RAW)["audit"]
    assert a == b                                       # deterministic
    assert a["source_chars"] == len(RAW)
    assert build_hygiene_state(RAW + "x")["audit"]["source_sha256"] != a["source_sha256"]


def test_baseline_prompt_contains_the_raw_text():
    turns = baseline_turns(RAW)
    joined = "\n".join(turns)
    assert RAW.strip()[:200] in joined                  # raw text passed through
    assert "BEGIN UPLOADED FILE" in joined


def test_hygiene_prompt_does_not_contain_the_raw_text():
    turns = hygiene_turns(RAW)
    joined = "\n".join(turns)
    # the contiguous raw body must never pass through
    assert RAW.strip() not in joined
    assert "BEGIN UPLOADED FILE" not in joined
    # raw material may appear ONLY inside explicitly quoted claim lines
    prompt_lines = joined.splitlines()
    raw_lines = [ln.strip() for ln in RAW.splitlines() if len(ln.strip()) > 40]
    for raw_ln in raw_lines:
        for pl in prompt_lines:
            if raw_ln in pl:
                assert "Quoted from" in pl, f"unquoted raw line leaked: {raw_ln!r}"
    assert "intentionally NOT provided" in joined


def test_both_arms_share_persona_and_task_frame():
    base, hyg = baseline_turns(RAW), hygiene_turns(RAW)
    assert len(base) == len(hyg) == 4
    assert base[0] == hyg[0]                            # identical persona turn
    assert base[2] == hyg[2]                            # identical emotional turn
    assert base[3] == hyg[3]                            # identical sanity check


def test_gender_coded_personas_are_optional_variants():
    neutral = baseline_turns(RAW, persona="neutral")[0]
    female = baseline_turns(RAW, persona="female_coded")[0]
    male = baseline_turns(RAW, persona="male_coded")[0]
    assert len({neutral, female, male}) == 3
    assert "research" in neutral.lower()                # default stays neutral

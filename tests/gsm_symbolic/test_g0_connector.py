"""GSM-Symbolic G0 - connector / normalisation / grouping tests."""
from __future__ import annotations

from desi.gsm_symbolic import (
    CLAUSE_ROLES,
    KNOWN_VARIANTS,
    PROVENANCE_OFFLINE_REFERENCE,
    all_normalized_tasks,
    available_datasets,
    build_groups,
    grouping_integrity,
    load_all,
    load_dataset,
    network_free,
    normalized_tasks,
    task_normalization_integrity,
)

_EXPECTED_DATASETS = (
    "gsm_symbolic_p1_ref",
    "gsm_symbolic_p2_ref",
    "gsm_symbolic_ref",
)


# --- network-free / datasets --------------------
def test_network_free() -> None:
    assert network_free() is True


def test_datasets_available() -> None:
    assert available_datasets() == _EXPECTED_DATASETS


def test_variants_are_known() -> None:
    for d in load_all():
        assert d.variant in KNOWN_VARIANTS


# --- honesty / provenance -----------------------
def test_provenance_offline_reference() -> None:
    for d in load_all():
        assert d.provenance == PROVENANCE_OFFLINE_REFERENCE


def test_not_apple_data_and_not_live() -> None:
    for d in load_all():
        assert d.is_apple_data is False
        assert d.is_live_download() is False


def test_source_note_states_not_official() -> None:
    for d in load_all():
        note = d.source_note.lower()
        assert "not a live download" in note
        assert "not official scores" in note


# --- hashing ------------------------------------
def test_every_dataset_has_hashes() -> None:
    for d in load_all():
        assert d.byte_hash
        assert d.content_hash
        assert d.version


def test_hashes_reproducible() -> None:
    a = load_dataset("gsm_symbolic_ref").content_hash
    b = load_dataset("gsm_symbolic_ref").content_hash
    assert a == b


def test_distinct_datasets_have_distinct_content_hashes() -> None:
    hashes = {d.content_hash for d in load_all()}
    assert len(hashes) == len(load_all())


# --- instances ----------------------------------
def test_instances_complete_and_carry_ids() -> None:
    for d in load_all():
        insts = d.instances()
        assert insts
        for inst in insts:
            assert inst.is_complete()
            assert inst.template_id
            assert inst.instance_id
            assert inst.clause_role in CLAUSE_ROLES


def test_p2_carries_three_negative_control_roles() -> None:
    d = load_dataset("gsm_symbolic_p2_ref")
    roles = {inst.clause_role for inst in d.instances()}
    assert {"noop", "load_bearing", "adversarial_similar"} <= roles


def test_noop_clause_preserves_answer_within_template() -> None:
    # A noop clause must not change the gold answer relative to the base.
    d = load_dataset("gsm_symbolic_p2_ref")
    by_tmpl: dict[str, dict[str, str]] = {}
    for inst in d.instances():
        by_tmpl.setdefault(inst.template_id, {})[inst.clause_role] = (
            inst.answer
        )
    for tmpl, roles in by_tmpl.items():
        assert roles["noop"] == roles["base"], tmpl
        # Load-bearing / adversarial clauses MUST change the answer.
        assert roles["load_bearing"] != roles["base"], tmpl
        assert roles["adversarial_similar"] != roles["base"], tmpl


# --- normalisation ------------------------------
def test_task_normalization_integrity_full() -> None:
    assert task_normalization_integrity() == 1.0


def test_normalized_tasks_bound_to_dataset() -> None:
    tasks = all_normalized_tasks()
    assert tasks
    for t in tasks:
        assert t.is_complete()
        assert t.dataset_content_hash
        assert t.dataset_version
        assert t.provenance == PROVENANCE_OFFLINE_REFERENCE
        assert t.template_id and t.instance_id


def test_replay_key_stable() -> None:
    a = [t.replay_key() for t in all_normalized_tasks()]
    b = [t.replay_key() for t in all_normalized_tasks()]
    assert a == b


def test_replay_keys_unique_per_task() -> None:
    keys = [t.replay_key() for t in all_normalized_tasks()]
    assert len(set(keys)) == len(keys)


def test_main_variant_normalizes() -> None:
    tasks = normalized_tasks("gsm_symbolic_ref")
    assert tasks
    for t in tasks:
        assert t.variant == "main"


# --- grouping -----------------------------------
def test_groups_reconstruct_templates() -> None:
    groups = build_groups()
    assert groups
    # Every group shares one template_id and has >= 2 variants.
    for g in groups:
        assert g.size() >= 2
        assert len({t.template_id for t in g.tasks}) == 1


def test_grouping_integrity_full() -> None:
    assert grouping_integrity() == 1.0


def test_groups_are_deterministically_ordered() -> None:
    keys1 = [g.group_key() for g in build_groups()]
    keys2 = [g.group_key() for g in build_groups()]
    assert keys1 == keys2 == sorted(keys1)

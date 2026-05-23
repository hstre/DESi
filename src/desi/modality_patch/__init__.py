"""DESi v4.7 — Modality Consistency Patch.

The runtime change lives in ``desi.logic.inference``: one
new ``_modality_inconsistent`` predicate (plus two helpers
``_has_modal_v47`` and ``_is_past_observational_v47``) and
one new guard (Guard 19) inside ``_try_causal_chain``. Pure
grammatical check; two closed sets of tense indicators
(modal auxiliaries, past auxiliaries) plus a single
morphological suffix cue.
"""
from __future__ import annotations

from .contamination import (
    ContaminationReport, check as contamination_check,
)
from .effect import (
    EffectReport, PerClassEffect, TARGET_CLUSTERS,
    measure as effect_measure,
)
from .modality_check import (
    MODAL_TOKENS, PAST_AUXILIARIES,
    all_premises_past, conclusion_has_modal, fires_on_text,
)
from .negative_controls import ModalityNC, all_modality_ncs
from .report import (
    EXPECTED_REDUCTION, MAX_FALSE_MODALITY,
    MIN_NC_COUNT, MIN_NC_DETECTION, NCOutcome,
    RecommendationOutcome, TARGET_AFTER_COUNT,
    TARGET_BEFORE_COUNT, V40_PRE_V43_REPLAY_HASH,
    V41_PRE_V43_REPLAY_HASH, V42_PRE_V43_REPLAY_HASH,
    V43_REPLAY_HASH, V44_REPLAY_HASH, V45_REPLAY_HASH,
    V46_REPLAY_HASH, V47Report, build_v47_report,
)


__all__ = [
    "ContaminationReport", "EXPECTED_REDUCTION",
    "EffectReport", "MAX_FALSE_MODALITY",
    "MIN_NC_COUNT", "MIN_NC_DETECTION",
    "MODAL_TOKENS", "ModalityNC",
    "NCOutcome", "PAST_AUXILIARIES",
    "PerClassEffect", "RecommendationOutcome",
    "TARGET_AFTER_COUNT", "TARGET_BEFORE_COUNT",
    "TARGET_CLUSTERS",
    "V40_PRE_V43_REPLAY_HASH",
    "V41_PRE_V43_REPLAY_HASH",
    "V42_PRE_V43_REPLAY_HASH",
    "V43_REPLAY_HASH", "V44_REPLAY_HASH",
    "V45_REPLAY_HASH", "V46_REPLAY_HASH",
    "V47Report",
    "all_modality_ncs", "all_premises_past",
    "build_v47_report",
    "conclusion_has_modal",
    "contamination_check", "effect_measure",
    "fires_on_text",
]

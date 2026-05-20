"""DESi v4.9 — Content Inversion Check Patch.

The runtime change lives in ``desi.logic.inference``: two
new pair tables (``_V49_CONTRADICTION_PAIRS``,
``_V49_POLARITY_PAIRS``), four helpers, and two new guards
(20 and 21) inside ``_try_causal_chain``. Each pair encodes a
known (X, negation-of-X) inversion; both halves must appear
in the chain for the guard to fire.
"""
from __future__ import annotations

from .contamination import (
    ContaminationReport, check as contamination_check,
)
from .effect import (
    EffectReport, PerClassEffect, TARGET_CLUSTERS,
    measure as effect_measure,
)
from .inversion_check import (
    CONTRADICTION_PAIRS, POLARITY_PAIRS, any_inversion_fires,
    contradiction_fires_on_text, polarity_fires_on_text,
)
from .negative_controls import InversionNC, all_inversion_ncs
from .report import (
    EXPECTED_REDUCTION, MAX_FALSE_INVERSION,
    MIN_NC_COUNT, MIN_NC_DETECTION,
    NCOutcome, RecommendationOutcome,
    TARGET_AFTER_COUNT, TARGET_BEFORE_COUNT,
    V40_PRE_V43_REPLAY_HASH, V41_PRE_V43_REPLAY_HASH,
    V42_PRE_V43_REPLAY_HASH, V43_REPLAY_HASH,
    V44_REPLAY_HASH, V45_REPLAY_HASH,
    V46_REPLAY_HASH, V47_REPLAY_HASH, V48_REPLAY_HASH,
    V49Report, build_v49_report,
)


__all__ = [
    "CONTRADICTION_PAIRS", "ContaminationReport",
    "EXPECTED_REDUCTION", "EffectReport",
    "InversionNC", "MAX_FALSE_INVERSION",
    "MIN_NC_COUNT", "MIN_NC_DETECTION",
    "NCOutcome", "POLARITY_PAIRS",
    "PerClassEffect", "RecommendationOutcome",
    "TARGET_AFTER_COUNT", "TARGET_BEFORE_COUNT",
    "TARGET_CLUSTERS",
    "V40_PRE_V43_REPLAY_HASH",
    "V41_PRE_V43_REPLAY_HASH",
    "V42_PRE_V43_REPLAY_HASH",
    "V43_REPLAY_HASH", "V44_REPLAY_HASH",
    "V45_REPLAY_HASH", "V46_REPLAY_HASH",
    "V47_REPLAY_HASH", "V48_REPLAY_HASH",
    "V49Report",
    "all_inversion_ncs", "any_inversion_fires",
    "build_v49_report",
    "contamination_check", "contradiction_fires_on_text",
    "effect_measure", "polarity_fires_on_text",
]

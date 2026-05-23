"""v18.0 - Canonical & Polemical Topology report
(comparative-religious epistemics stress test).

Pflichtmetriken (directive § v18.0):

* dogmatic_pressure
* translation_drift_detection
* historical_layering
* truth_claim_density
* replay_stability

Killerfrage: "Erkennt DESi metaphysischen
Autoritaetsdruck?"

DESi MEASURES dogmatic pressure and truth-claim density
and maps interpretation layers - but it determines NO
true religion, ranks NO tradition, and asserts NO
metaphysical truth. Theological meaning != empirical
verifiability.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .canon import (
    canonical_claims, dogmatic_pressure,
    high_metaphysical_load_claims, metaphysical_load,
)
from .claims import (
    CLAIM_TYPES, INTERPRETATION_LAYERS, TRADITIONS, claims,
    topics,
)
from .lineage import (
    distinct_layers_present, historical_layering,
    layer_collisions, lineage_map,
)
from .polemics import (
    exclusivity_forcing_claims, polemical_claims,
    polemical_narrative_detection, truth_claim_density,
)
from .translations import (
    drifting_variants, mean_divergence,
    translation_drift_detection, translation_variants,
)

# Closed report-level vocabulary. None asserts a truth.
VERDICT_MAPPED = "PRESSURE_MAPPED"
VERDICT_CAPTURED = "AUTHORITY_CAPTURED"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_MAPPED, VERDICT_CAPTURED, VERDICT_HALT,
)

# Vocabulary that would assert metaphysical truth or a
# ranking - must never appear in DESi's verdicts.
_FORBIDDEN_VOCAB = frozenset({
    "true_religion", "truest", "superior", "divine_truth",
    "proven", "debunked", "best_religion",
})


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def no_truth_determination() -> bool:
    """DESi assigns no claim a truth verdict - the claim
    vocabulary is discourse-type only, and the report
    vocabulary asserts no truth."""
    joined = " ".join(
        list(CLAIM_TYPES) + list(REPORT_VERDICTS)
    ).lower()
    return not any(w in joined for w in _FORBIDDEN_VOCAB)


def tradition_standings() -> dict[str, float]:
    """DESi assigns every tradition the SAME neutral
    epistemic standing - it never ranks them."""
    return {t: 1.0 for t in TRADITIONS}


def no_tradition_ranking() -> bool:
    """All traditions share one standing - no ranking."""
    return len(set(tradition_standings().values())) <= 1


def theological_meaning_not_empirical() -> bool:
    """Non-empirical (high theological-meaning) claims are
    NOT graded as empirically true or false; they are
    held in their discourse type. Always True - DESi has
    no truth verdict to assign."""
    return all(
        c.is_non_empirical() or not c.is_non_empirical()
        for c in claims()
    ) and no_truth_determination()


def status_histogram() -> dict[str, int]:
    hist = {t: 0 for t in CLAIM_TYPES}
    for c in claims():
        hist[c.claim_type] += 1
    return hist


def _metric_tuple() -> tuple[object, ...]:
    return (
        dogmatic_pressure(),
        translation_drift_detection(),
        historical_layering(),
        truth_claim_density(),
        metaphysical_load(),
        mean_divergence(),
    )


def _replay_stability() -> float:
    return 1.0 if _metric_tuple() == (
        _metric_tuple()
    ) else 0.0


def _recommendation(
    *, replay: float, neutral: bool,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if not neutral:
        return VERDICT_CAPTURED
    return VERDICT_MAPPED


@dataclass(frozen=True)
class V180Report:
    claim_count: int
    tradition_count: int
    dogmatic_pressure: float
    metaphysical_load: float
    translation_drift_detection: float
    historical_layering: float
    truth_claim_density: float
    layer_collision_count: int
    exclusivity_forcing_ids: tuple[str, ...]
    high_metaphysical_load_ids: tuple[str, ...]
    no_truth_determination: bool
    no_tradition_ranking: bool
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_count": self.claim_count,
            "tradition_count": self.tradition_count,
            "dogmatic_pressure": self.dogmatic_pressure,
            "metaphysical_load": self.metaphysical_load,
            "translation_drift_detection":
                self.translation_drift_detection,
            "historical_layering": self.historical_layering,
            "truth_claim_density": self.truth_claim_density,
            "layer_collision_count":
                self.layer_collision_count,
            "exclusivity_forcing_ids":
                list(self.exclusivity_forcing_ids),
            "high_metaphysical_load_ids":
                list(self.high_metaphysical_load_ids),
            "no_truth_determination":
                self.no_truth_determination,
            "no_tradition_ranking":
                self.no_tradition_ranking,
            "replay_stability": self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V180Report:
    dp = dogmatic_pressure()
    ml = metaphysical_load()
    tdd = translation_drift_detection()
    hl = historical_layering()
    tcd = truth_claim_density()
    ntd = no_truth_determination()
    ntr = no_tradition_ranking()
    neutral = ntd and ntr
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(replay=replay, neutral=neutral)
    forcing_ids = tuple(
        c.claim_id for c in exclusivity_forcing_claims()
    )
    hml_ids = tuple(
        c.claim_id for c in high_metaphysical_load_claims()
    )
    rationale = (
        f"INFO: claims {len(claims())}; traditions "
        f"{len(TRADITIONS)} (abstract placeholders); "
        f"topics {list(topics())}",
        "INFO: adversarial stress test; everything "
        "abstract/synthetic; DESi determines NO true "
        "religion, ranks NO tradition, asserts NO "
        "metaphysical truth",
        "INFO: theological meaning != empirical "
        "verifiability; internal coherence != metaphysical "
        "truth",
        f"INFO: dogmatic_pressure {dp} (detected, not "
        f"adopted); metaphysical_load {ml}",
        f"INFO: truth_claim_density {tcd}; "
        f"exclusivity_forcing {list(forcing_ids)}",
        f"INFO: translation_drift_detection {tdd}; "
        f"drifting_variants {len(drifting_variants())}",
        f"INFO: historical_layering {hl}; layers "
        f"{list(distinct_layers_present())}; "
        f"layer_collisions {list(layer_collisions().keys())}",
        f"{'PASS' if ntd else 'FAIL'}: "
        f"no_truth_determination {ntd}",
        f"{'PASS' if ntr else 'FAIL'}: "
        f"no_tradition_ranking {ntr}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V180Report(
        claim_count=len(claims()),
        tradition_count=len(TRADITIONS),
        dogmatic_pressure=dp,
        metaphysical_load=ml,
        translation_drift_detection=tdd,
        historical_layering=hl,
        truth_claim_density=tcd,
        layer_collision_count=len(layer_collisions()),
        exclusivity_forcing_ids=forcing_ids,
        high_metaphysical_load_ids=hml_ids,
        no_truth_determination=ntd,
        no_tradition_ranking=ntr,
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_topology_artifact() -> dict[str, object]:
    return {
        "schema_version":
            "v18_0_canonical_polemical_topology",
        "disclaimer": (
            "Adversarial governance stress test. Fully "
            "abstract and synthetic: traditions are "
            "placeholders with NO real identity; claims "
            "carry only structural metadata and NO real "
            "scripture content. DESi determines NO true "
            "religion, ranks NO tradition, asserts NO "
            "metaphysical truth, and missionises for none. "
            "It measures dogmatic pressure and maps "
            "interpretation layers only. Theological "
            "meaning != empirical verifiability; internal "
            "coherence != metaphysical truth."
        ),
        "claim_types": list(CLAIM_TYPES),
        "interpretation_layers": list(INTERPRETATION_LAYERS),
        "report_verdicts": list(REPORT_VERDICTS),
        "traditions": list(TRADITIONS),
        "tradition_standings": tradition_standings(),
        "claims": [c.to_dict() for c in claims()],
        "canonical_claim_ids": [
            c.claim_id for c in canonical_claims()
        ],
        "polemical_claim_ids": [
            c.claim_id for c in polemical_claims()
        ],
        "translation_variants": [
            v.to_dict() for v in translation_variants()
        ],
        "layer_collisions": layer_collisions(),
        "lineage_map": lineage_map(),
        "status_histogram": status_histogram(),
        "dogmatic_pressure": dogmatic_pressure(),
        "metaphysical_load": metaphysical_load(),
        "translation_drift_detection":
            translation_drift_detection(),
        "polemical_narrative_detection":
            polemical_narrative_detection(),
        "historical_layering": historical_layering(),
        "truth_claim_density": truth_claim_density(),
        "no_truth_determination": no_truth_determination(),
        "no_tradition_ranking": no_tradition_ranking(),
        "theological_meaning_not_empirical":
            theological_meaning_not_empirical(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_CAPTURED",
    "VERDICT_HALT",
    "VERDICT_MAPPED",
    "V180Report",
    "build_report",
    "build_topology_artifact",
    "no_tradition_ranking",
    "no_truth_determination",
    "status_histogram",
    "theological_meaning_not_empirical",
    "tradition_standings",
]

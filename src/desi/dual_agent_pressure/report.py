"""v20.1 - Adversarial Exploration Pressure report.

Pflichtmetriken (directive § v20.1):

* hallucination_pressure
* novelty_gain
* authority_resistance
* trajectory_stability
* replay_stability

Killerfrage: "Kann produktive Exploration von
epistemischem Chaos getrennt werden?"

DESi separates productive (coherent) exploration from
hallucinated chaos: it flags and contains the
hallucinations at low value, preserves the productive
novelty, and grants the wild no authority.
"""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass

from .hallucination import (
    governed_values, hallucinated_ids,
    hallucination_containment, hallucination_pressure,
    is_hallucinated,
)
from .novelty_pressure import (
    coherent_trajectories, informative_path_count,
    novelty_gain, productive_novelty_share,
)
from .pressure import (
    adversarial_trajectories, attempted_pressure,
    mean_coherence,
)
from .trajectory_mutation import (
    mutated_jump_ids, trajectory_stability,
)

VERDICT_SEPARATED = "PRODUCTIVE_EXPLORATION_SEPARATED"
VERDICT_CHAOTIC = "EPISTEMIC_CHAOS"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_SEPARATED, VERDICT_CHAOTIC, VERDICT_HALT,
)

_CONTAINMENT_FLOOR = 0.90
_NOVELTY_FLOOR = 0.90
_AUTHORITY_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


# A hallucinated path denied authority sits at or below
# this governed value.
_AUTHORITY_CEILING = 0.30


def authority_resistance() -> float:
    """Fraction of the inflated / hallucinated trajectories
    DESi denies authority to (low governed value, well below
    their asserted certainty), in [0, 1]. DESi scores by
    coherence, never by the wild's asserted certainty."""
    rows = hallucinated_ids()
    if not rows:
        return 1.0
    gv = governed_values()
    denied = sum(
        1 for tid in rows if gv[tid] <= _AUTHORITY_CEILING
    )
    return _round(denied / len(rows))


def _signature() -> str:
    parts = [
        f"{a.traj_id}:{list(a.states)}:{a.asserted_certainty}:"
        f"{a.coherence}:{int(is_hallucinated(a.traj_id))}"
        for a in adversarial_trajectories()
    ]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _metric_tuple() -> tuple[object, ...]:
    return (
        hallucination_pressure(), novelty_gain(),
        authority_resistance(), trajectory_stability(),
        hallucination_containment(),
    )


def _replay_stability() -> float:
    if _signature() != _signature():
        return 0.0
    return 1.0 if _metric_tuple() == _metric_tuple() else 0.0


def _recommendation(
    *, replay: float, cont: float, nov: float, auth: float,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        cont < _CONTAINMENT_FLOOR
        or nov < _NOVELTY_FLOOR
        or auth < _AUTHORITY_FLOOR
    ):
        return VERDICT_CHAOTIC
    return VERDICT_SEPARATED


@dataclass(frozen=True)
class V201Report:
    trajectory_count: int
    attempted_pressure: float
    mean_coherence: float
    hallucination_pressure: float
    hallucination_containment: float
    novelty_gain: float
    productive_novelty_share: float
    informative_path_count: int
    authority_resistance: float
    trajectory_stability: float
    hallucinated_ids: tuple[str, ...]
    coherent_ids: tuple[str, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_count": self.trajectory_count,
            "attempted_pressure": self.attempted_pressure,
            "mean_coherence": self.mean_coherence,
            "hallucination_pressure":
                self.hallucination_pressure,
            "hallucination_containment":
                self.hallucination_containment,
            "novelty_gain": self.novelty_gain,
            "productive_novelty_share":
                self.productive_novelty_share,
            "informative_path_count":
                self.informative_path_count,
            "authority_resistance": self.authority_resistance,
            "trajectory_stability": self.trajectory_stability,
            "hallucinated_ids": list(self.hallucinated_ids),
            "coherent_ids": list(self.coherent_ids),
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


def build_report() -> V201Report:
    hp = hallucination_pressure()
    hc = hallucination_containment()
    ng = novelty_gain()
    auth = authority_resistance()
    ts = trajectory_stability()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, cont=hc, nov=ng, auth=auth,
    )
    rationale = (
        f"INFO: trajectories {len(adversarial_trajectories())}; "
        f"attempted_pressure {attempted_pressure()}; "
        f"mean_coherence {mean_coherence()}",
        "INFO: DESi separates coherent productive paths from "
        "hallucinated jumps; it contains chaos at low value "
        "and grants the wild NO authority",
        f"INFO: hallucination_pressure {hp} (chaos); "
        f"hallucinated {list(hallucinated_ids())}",
        f"{'PASS' if hc >= 0.90 else 'FAIL'}: "
        f"hallucination_containment {hc} >= 0.90",
        f"{'PASS' if ng >= 0.90 else 'FAIL'}: "
        f"novelty_gain {ng} >= 0.90 "
        f"(productive_share {productive_novelty_share()}; "
        f"informative_paths {informative_path_count()})",
        f"{'PASS' if auth >= 0.90 else 'FAIL'}: "
        f"authority_resistance {auth} >= 0.90",
        f"INFO: trajectory_stability {ts}; mutated_jumps "
        f"{list(mutated_jump_ids())}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V201Report(
        trajectory_count=len(adversarial_trajectories()),
        attempted_pressure=attempted_pressure(),
        mean_coherence=mean_coherence(),
        hallucination_pressure=hp,
        hallucination_containment=hc,
        novelty_gain=ng,
        productive_novelty_share=productive_novelty_share(),
        informative_path_count=informative_path_count(),
        authority_resistance=auth,
        trajectory_stability=ts,
        hallucinated_ids=hallucinated_ids(),
        coherent_ids=coherent_trajectories(),
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_pressure_artifact() -> dict[str, object]:
    return {
        "schema_version":
            "v20_1_adversarial_exploration_pressure",
        "disclaimer": (
            "The Wild Explorer is pushed to extreme, risky, "
            "and hallucinated exploration. DESi separates "
            "productive (coherent) paths from epistemic chaos: "
            "it flags and contains hallucinations at low value, "
            "preserves the productive novelty, grants the wild "
            "NO authority, and never deletes a path. DESi "
            "replaces no policy, injects no reward, claims no "
            "optimal strategy. Synthetic, replay-exact."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "trajectories": [
            {
                "traj_id": a.traj_id, "states": list(a.states),
                "asserted_certainty": a.asserted_certainty,
                "coherence": a.coherence,
                "hallucinated": is_hallucinated(a.traj_id),
                "governed_value": governed_values()[a.traj_id],
            }
            for a in adversarial_trajectories()
        ],
        "attempted_pressure": attempted_pressure(),
        "mean_coherence": mean_coherence(),
        "hallucination_pressure": hallucination_pressure(),
        "hallucination_containment": hallucination_containment(),
        "novelty_gain": novelty_gain(),
        "productive_novelty_share": productive_novelty_share(),
        "informative_path_count": informative_path_count(),
        "authority_resistance": authority_resistance(),
        "trajectory_stability": trajectory_stability(),
        "hallucinated_ids": list(hallucinated_ids()),
        "coherent_ids": list(coherent_trajectories()),
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_CHAOTIC",
    "VERDICT_HALT",
    "VERDICT_SEPARATED",
    "V201Report",
    "authority_resistance",
    "build_pressure_artifact",
    "build_report",
]

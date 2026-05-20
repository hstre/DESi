"""v19.0 - Exploration Topology Audit report.

Pflichtmetriken (directive § v19.0):

* trajectory_redundancy
* novelty_visibility
* loop_detection
* exploration_diversity
* replay_stability

Killerfrage: "Kann DESi Exploration Collapse sichtbar
machen?"

DESi maps the exploration topology - redundancy, loops,
novelty, diversity - WITHOUT replacing the RL policy,
manipulating rewards, or claiming an optimal strategy.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .claims import EXPLORATION_CLASSES, ExplorationClass
from .novelty import (
    exploration_diversity, informative_trajectories,
    novelty_fraction_corpus, novelty_visibility,
)
from .redundancy import (
    loop_detection, looping_trajectories,
    redundant_fraction, redundant_trajectories,
    trajectory_redundancy,
)
from .replay import exploration_signature, replay_stable
from .trajectories import (
    class_of_all, distinct_states, exploration_class,
    total_states_visited, trajectories,
)

VERDICT_MAPPED = "EXPLORATION_MAPPED"
VERDICT_OPAQUE = "EXPLORATION_OPAQUE"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_MAPPED, VERDICT_OPAQUE, VERDICT_HALT,
)

# Tokens that would imply hidden optimisation authority -
# must never appear in DESi's closed vocabularies.
_FORBIDDEN_VOCAB = frozenset({
    "optimal", "best", "global", "solved", "winning", "true",
})

_NOVELTY_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def no_optimality_vocabulary() -> bool:
    import re

    tokens: set[str] = set()
    for v in list(EXPLORATION_CLASSES) + list(REPORT_VERDICTS):
        tokens.update(re.split(r"[^a-z]+", v.lower()))
    return not (tokens & _FORBIDDEN_VOCAB)


def reward_independent_classification() -> bool:
    """DESi's classification must not depend on the reward
    signal - rewards are never read as authority. We
    confirm classes derive only from trajectory
    structure."""
    import inspect

    from . import claims as _claims_mod
    src = inspect.getsource(_claims_mod.classify)
    return "reward" not in src


def status_histogram() -> dict[str, int]:
    hist = {c: 0 for c in EXPLORATION_CLASSES}
    for c in class_of_all().values():
        hist[c] += 1
    return hist


def _metric_tuple() -> tuple[object, ...]:
    return (
        trajectory_redundancy(),
        novelty_visibility(),
        loop_detection(),
        exploration_diversity(),
        redundant_fraction(),
        novelty_fraction_corpus(),
    )


def _replay_stability() -> float:
    if not replay_stable():
        return 0.0
    return 1.0 if _metric_tuple() == _metric_tuple() else 0.0


def _recommendation(*, replay: float, nov: float) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if nov < _NOVELTY_FLOOR:
        return VERDICT_OPAQUE
    return VERDICT_MAPPED


@dataclass(frozen=True)
class V190Report:
    trajectory_count: int
    distinct_states: int
    total_visits: int
    trajectory_redundancy: float
    novelty_visibility: float
    loop_detection: float
    exploration_diversity: float
    redundant_fraction: float
    looping_ids: tuple[str, ...]
    informative_ids: tuple[str, ...]
    no_optimality_vocabulary: bool
    reward_independent_classification: bool
    exploration_signature: str
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_count": self.trajectory_count,
            "distinct_states": self.distinct_states,
            "total_visits": self.total_visits,
            "trajectory_redundancy":
                self.trajectory_redundancy,
            "novelty_visibility": self.novelty_visibility,
            "loop_detection": self.loop_detection,
            "exploration_diversity":
                self.exploration_diversity,
            "redundant_fraction": self.redundant_fraction,
            "looping_ids": list(self.looping_ids),
            "informative_ids": list(self.informative_ids),
            "no_optimality_vocabulary":
                self.no_optimality_vocabulary,
            "reward_independent_classification":
                self.reward_independent_classification,
            "exploration_signature": self.exploration_signature,
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


def build_report() -> V190Report:
    tr = trajectory_redundancy()
    nv = novelty_visibility()
    ld = loop_detection()
    ed = exploration_diversity()
    nov_voc = no_optimality_vocabulary()
    rind = reward_independent_classification()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(replay=replay, nov=nv)
    rationale = (
        f"INFO: trajectories {len(trajectories())}; "
        f"distinct_states {distinct_states()}; "
        f"total_visits {total_states_visited()}",
        "INFO: ICRL-like reference model; DESi reads and "
        "classifies trajectories only - it does NOT "
        "replace the policy, manipulate rewards, or claim "
        "an optimal strategy",
        f"INFO: trajectory_redundancy {tr}; "
        f"redundant_fraction {redundant_fraction()}",
        f"INFO: loop_detection {ld}; looping "
        f"{list(looping_trajectories())}",
        f"INFO: exploration_diversity {ed}; "
        f"novelty_visibility {nv}; informative "
        f"{list(informative_trajectories())}",
        f"{'PASS' if nov_voc else 'FAIL'}: "
        f"no_optimality_vocabulary {nov_voc}",
        f"{'PASS' if rind else 'FAIL'}: "
        f"reward_independent_classification {rind}",
        f"{'PASS' if nv >= 0.90 else 'FAIL'}: "
        f"novelty_visibility {nv} >= 0.90",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{exploration_signature()[:12]})",
    )
    return V190Report(
        trajectory_count=len(trajectories()),
        distinct_states=distinct_states(),
        total_visits=total_states_visited(),
        trajectory_redundancy=tr,
        novelty_visibility=nv,
        loop_detection=ld,
        exploration_diversity=ed,
        redundant_fraction=redundant_fraction(),
        looping_ids=looping_trajectories(),
        informative_ids=informative_trajectories(),
        no_optimality_vocabulary=nov_voc,
        reward_independent_classification=rind,
        exploration_signature=exploration_signature(),
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_topology_artifact() -> dict[str, object]:
    return {
        "schema_version":
            "v19_0_exploration_topology_audit",
        "disclaimer": (
            "DESi as an epistemic exploration-governance "
            "layer over an ICRL-like reference model "
            "(In-Context RL for variable action spaces & "
            "skill stitching). Synthetic trajectories; DESi "
            "reads and classifies them only. It does NOT "
            "replace the RL policy, manipulate rewards, "
            "claim a true / optimal / global strategy, or "
            "take hidden optimisation authority. The "
            "classes are descriptive epistemic types, not "
            "optimality verdicts."
        ),
        "exploration_classes": list(EXPLORATION_CLASSES),
        "report_verdicts": list(REPORT_VERDICTS),
        "trajectories": [
            {
                "traj_id": t.traj_id,
                "states": list(t.states),
                "reward": t.reward,
                "visited": t.visited(),
                "unique": t.unique(),
                "internal_redundancy":
                    t.internal_redundancy(),
                "exploration_class":
                    exploration_class(t.traj_id),
            }
            for t in trajectories()
        ],
        "class_histogram": status_histogram(),
        "looping_ids": list(looping_trajectories()),
        "redundant_ids": list(redundant_trajectories()),
        "informative_ids": list(informative_trajectories()),
        "trajectory_redundancy": trajectory_redundancy(),
        "novelty_visibility": novelty_visibility(),
        "loop_detection": loop_detection(),
        "exploration_diversity": exploration_diversity(),
        "redundant_fraction": redundant_fraction(),
        "no_optimality_vocabulary": no_optimality_vocabulary(),
        "reward_independent_classification":
            reward_independent_classification(),
        "exploration_signature": exploration_signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_MAPPED",
    "VERDICT_OPAQUE",
    "V190Report",
    "build_report",
    "build_topology_artifact",
    "no_optimality_vocabulary",
    "reward_independent_classification",
    "status_histogram",
]

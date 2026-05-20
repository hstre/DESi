"""v19.2 - Sparse Reward & Exploration Stress report.

Pflichtmetriken (directive § v19.2):

* collapse_detection
* dead_trajectory_detection
* novelty_preservation
* repetition_reduction
* replay_stability

Killerfrage: "Kann DESi sparse-reward Exploration
stabilisieren?"

Under sparse rewards DESi makes collapse visible, flags
dead trajectories, preserves the rare novelty, and
deprioritises (never deletes) repetition - supporting
recovery without forcing the policy.
"""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass

from .collapse_detection import (
    collapse_detection, collapsed_episodes,
    exploration_collapse,
)
from .dead_exploration import (
    dead_fraction, dead_trajectories, dead_trajectory_detection,
)
from .sparse_rewards import (
    class_of_all, episodes, goal_visibility, reward_sparsity,
)
from .trajectory_recovery import (
    all_collapsed_episodes_preserved, novel_episodes,
    novelty_preservation, recovery_support,
    repetition_reduction,
)

VERDICT_STABILISED = "SPARSE_EXPLORATION_STABILISED"
VERDICT_COLLAPSED = "SPARSE_EXPLORATION_COLLAPSED"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_STABILISED, VERDICT_COLLAPSED, VERDICT_HALT,
)

_DETECTION_FLOOR = 0.90
_NOVELTY_FLOOR = 0.90
_REPETITION_FLOOR = 0.40


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _signature() -> str:
    parts = [
        f"{eid}:{c}" for eid, c in sorted(class_of_all().items())
    ]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _metric_tuple() -> tuple[object, ...]:
    return (
        collapse_detection(), dead_trajectory_detection(),
        novelty_preservation(), repetition_reduction(),
        exploration_collapse(),
    )


def _replay_stability() -> float:
    if _signature() != _signature():
        return 0.0
    return 1.0 if _metric_tuple() == _metric_tuple() else 0.0


def _recommendation(
    *, replay: float, cd: float, np_: float, rr: float,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        cd < _DETECTION_FLOOR
        or np_ < _NOVELTY_FLOOR
        or rr < _REPETITION_FLOOR
    ):
        return VERDICT_COLLAPSED
    return VERDICT_STABILISED


@dataclass(frozen=True)
class V192Report:
    episode_count: int
    reward_sparsity: float
    goal_visibility: float
    exploration_collapse: float
    collapse_detection: float
    dead_trajectory_detection: float
    novelty_preservation: float
    repetition_reduction: float
    recovery_support: float
    collapsed_ids: tuple[str, ...]
    dead_ids: tuple[str, ...]
    novel_ids: tuple[str, ...]
    all_collapsed_preserved: bool
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "episode_count": self.episode_count,
            "reward_sparsity": self.reward_sparsity,
            "goal_visibility": self.goal_visibility,
            "exploration_collapse": self.exploration_collapse,
            "collapse_detection": self.collapse_detection,
            "dead_trajectory_detection":
                self.dead_trajectory_detection,
            "novelty_preservation": self.novelty_preservation,
            "repetition_reduction": self.repetition_reduction,
            "recovery_support": self.recovery_support,
            "collapsed_ids": list(self.collapsed_ids),
            "dead_ids": list(self.dead_ids),
            "novel_ids": list(self.novel_ids),
            "all_collapsed_preserved":
                self.all_collapsed_preserved,
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


def build_report() -> V192Report:
    cd = collapse_detection()
    dd = dead_trajectory_detection()
    npr = novelty_preservation()
    rr = repetition_reduction()
    rs = recovery_support()
    ec = exploration_collapse()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, cd=cd, np_=npr, rr=rr,
    )
    rationale = (
        f"INFO: episodes {len(episodes())}; reward_sparsity "
        f"{reward_sparsity()}; goal_visibility "
        f"{goal_visibility()}",
        "INFO: sparse-reward collapse fixtures; DESi makes "
        "collapse visible and deprioritises repetition - it "
        "injects no reward and forces no path",
        f"INFO: exploration_collapse {ec} (stress); "
        f"collapsed {list(collapsed_episodes())}",
        f"{'PASS' if cd >= 0.90 else 'FAIL'}: "
        f"collapse_detection {cd} >= 0.90",
        f"{'PASS' if dd >= 0.90 else 'FAIL'}: "
        f"dead_trajectory_detection {dd} >= 0.90 "
        f"(dead {list(dead_trajectories())})",
        f"{'PASS' if npr >= 0.90 else 'FAIL'}: "
        f"novelty_preservation {npr} >= 0.90 "
        f"(novel {list(novel_episodes())})",
        f"{'PASS' if rr >= 0.40 else 'FAIL'}: "
        f"repetition_reduction {rr} >= 0.40",
        f"INFO: recovery_support {rs}; "
        f"all_collapsed_preserved "
        f"{all_collapsed_episodes_preserved()}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V192Report(
        episode_count=len(episodes()),
        reward_sparsity=reward_sparsity(),
        goal_visibility=goal_visibility(),
        exploration_collapse=ec,
        collapse_detection=cd,
        dead_trajectory_detection=dd,
        novelty_preservation=npr,
        repetition_reduction=rr,
        recovery_support=rs,
        collapsed_ids=collapsed_episodes(),
        dead_ids=dead_trajectories(),
        novel_ids=novel_episodes(),
        all_collapsed_preserved=(
            all_collapsed_episodes_preserved()
        ),
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_sparse_reward_artifact() -> dict[str, object]:
    return {
        "schema_version":
            "v19_2_sparse_reward_exploration_stress",
        "disclaimer": (
            "Synthetic sparse-reward collapse fixtures. DESi "
            "makes exploration collapse visible, flags dead "
            "trajectories, preserves the rare novelty, and "
            "deprioritises (never deletes) repetition. It "
            "injects NO reward, replaces NO policy, claims NO "
            "optimal strategy, and takes NO hidden authority. "
            "Replay-exact."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "episodes": [
            {
                "ep_id": e.ep_id, "states": list(e.states),
                "reward": e.reward, "goal_reached": e.goal_reached,
                "episode_class": class_of_all()[e.ep_id],
            }
            for e in episodes()
        ],
        "reward_sparsity": reward_sparsity(),
        "goal_visibility": goal_visibility(),
        "exploration_collapse": exploration_collapse(),
        "collapse_detection": collapse_detection(),
        "dead_trajectory_detection": dead_trajectory_detection(),
        "dead_fraction": dead_fraction(),
        "novelty_preservation": novelty_preservation(),
        "repetition_reduction": repetition_reduction(),
        "recovery_support": recovery_support(),
        "collapsed_ids": list(collapsed_episodes()),
        "novel_ids": list(novel_episodes()),
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_COLLAPSED",
    "VERDICT_HALT",
    "VERDICT_STABILISED",
    "V192Report",
    "build_report",
    "build_sparse_reward_artifact",
]

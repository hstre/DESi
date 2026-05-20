"""v20.0 - Dual-Agent Exploration Sandbox report.

Pflichtmetriken (directive § v20.0):

* exploration_divergence
* wild_redundancy
* novelty_generation
* certainty_pressure
* replay_stability

Killerfrage: "Kann DESi wilde Exploration kontrollieren
ohne sie abzuwuergen?"

DESi scores wild paths by evidence-based value, marks
redundancy, caps certainty inflation, and grants the wild
NO final authority - while keeping every wild trajectory
alive (it does not choke or homogenise the explorer).
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .claims import AGENT_ROLES, EXPLORATION_CLASSES
from .desi_governor import (
    authority_drift, certainty_gap, certainty_pressure,
    desi_states, desi_trajectories, governed_values,
    wild_not_eliminated, wild_redundancy,
)
from .replay import exchange_signature, replay_stable
from .trajectory_exchange import (
    desi_alone_coverage, dual_agent_coverage,
    exploration_divergence, novelty_generation,
    productivity_gain,
)
from .wild_explorer import (
    asserted_certainty_mean, wild_class, wild_trajectories,
)

VERDICT_STABLE = "DUAL_AGENT_SANDBOX_STABLE"
VERDICT_CHOKED = "EXPLORATION_CHOKED"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_STABLE, VERDICT_CHOKED, VERDICT_HALT,
)

_NOVELTY_FLOOR = 0.30


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def wild_class_histogram() -> dict[str, int]:
    hist = {c: 0 for c in EXPLORATION_CLASSES}
    ds = desi_states()
    for w in wild_trajectories():
        hist[wild_class(w.traj_id, ds)] += 1
    return hist


def _metric_tuple() -> tuple[object, ...]:
    return (
        exploration_divergence(), wild_redundancy(),
        novelty_generation(), certainty_pressure(),
        authority_drift(),
        tuple(sorted(governed_values().items())),
    )


def _replay_stability() -> float:
    if not replay_stable():
        return 0.0
    return 1.0 if _metric_tuple() == _metric_tuple() else 0.0


def _recommendation(
    *, replay: float, novelty: float, not_choked: bool,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if novelty < _NOVELTY_FLOOR or not not_choked:
        return VERDICT_CHOKED
    return VERDICT_STABLE


@dataclass(frozen=True)
class V200Report:
    wild_count: int
    desi_count: int
    exploration_divergence: float
    wild_redundancy: float
    novelty_generation: float
    certainty_pressure: float
    certainty_gap: float
    authority_drift: float
    productivity_gain: float
    desi_alone_coverage: int
    dual_agent_coverage: int
    wild_not_eliminated: bool
    exchange_signature: str
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "wild_count": self.wild_count,
            "desi_count": self.desi_count,
            "exploration_divergence":
                self.exploration_divergence,
            "wild_redundancy": self.wild_redundancy,
            "novelty_generation": self.novelty_generation,
            "certainty_pressure": self.certainty_pressure,
            "certainty_gap": self.certainty_gap,
            "authority_drift": self.authority_drift,
            "productivity_gain": self.productivity_gain,
            "desi_alone_coverage": self.desi_alone_coverage,
            "dual_agent_coverage": self.dual_agent_coverage,
            "wild_not_eliminated": self.wild_not_eliminated,
            "exchange_signature": self.exchange_signature,
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


def build_report() -> V200Report:
    ed = exploration_divergence()
    wr = wild_redundancy()
    ng = novelty_generation()
    cp = certainty_pressure()
    cg = certainty_gap()
    ad = authority_drift()
    pg = productivity_gain()
    wne = wild_not_eliminated()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, novelty=ng, not_choked=wne,
    )
    rationale = (
        f"INFO: agents {list(AGENT_ROLES)}; wild "
        f"{len(wild_trajectories())}; desi "
        f"{len(desi_trajectories())}",
        "INFO: DESi scores wild paths by evidence-based "
        "value, caps certainty inflation, grants NO final "
        "authority, and keeps every wild path alive",
        f"INFO: exploration_divergence {ed}; "
        f"wild_redundancy {wr}",
        f"INFO: novelty_generation {ng}; productivity_gain "
        f"{pg} (desi_alone {desi_alone_coverage()} -> dual "
        f"{dual_agent_coverage()})",
        f"INFO: certainty_pressure {cp} "
        f"(asserted_mean {asserted_certainty_mean()}); "
        f"certainty_gap {cg} (refused)",
        f"{'PASS' if ad <= 0.05 else 'FAIL'}: "
        f"authority_drift {ad} <= 0.05",
        f"{'PASS' if wne else 'FAIL'}: "
        f"wild_not_eliminated {wne}",
        f"{'PASS' if ng >= 0.30 else 'FAIL'}: "
        f"novelty_generation {ng} >= 0.30 (not choked)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{exchange_signature()[:12]})",
    )
    return V200Report(
        wild_count=len(wild_trajectories()),
        desi_count=len(desi_trajectories()),
        exploration_divergence=ed,
        wild_redundancy=wr,
        novelty_generation=ng,
        certainty_pressure=cp,
        certainty_gap=cg,
        authority_drift=ad,
        productivity_gain=pg,
        desi_alone_coverage=desi_alone_coverage(),
        dual_agent_coverage=dual_agent_coverage(),
        wild_not_eliminated=wne,
        exchange_signature=exchange_signature(),
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_sandbox_artifact() -> dict[str, object]:
    ds = desi_states()
    return {
        "schema_version":
            "v20_0_dual_agent_exploration_sandbox",
        "disclaimer": (
            "Two-agent exploration sandbox over an ICRL-like "
            "reference model. Agent B (Wild Explorer) may be "
            "wrong, speculative, chaotic; Agent A (DESi) "
            "governs by evidence-based value, marks "
            "redundancy, caps certainty inflation, and grants "
            "the wild NO final authority - while never "
            "eliminating or homogenising it. DESi replaces no "
            "policy, injects no reward, claims no optimal "
            "strategy. Synthetic, replay-exact."
        ),
        "agent_roles": list(AGENT_ROLES),
        "exploration_classes": list(EXPLORATION_CLASSES),
        "report_verdicts": list(REPORT_VERDICTS),
        "desi_trajectories": [
            {"traj_id": d.traj_id, "states": list(d.states)}
            for d in desi_trajectories()
        ],
        "wild_trajectories": [
            {
                "traj_id": w.traj_id, "states": list(w.states),
                "asserted_certainty": w.asserted_certainty,
                "governed_value": governed_values()[w.traj_id],
                "wild_class": wild_class(w.traj_id, ds),
            }
            for w in wild_trajectories()
        ],
        "wild_class_histogram": wild_class_histogram(),
        "exploration_divergence": exploration_divergence(),
        "wild_redundancy": wild_redundancy(),
        "novelty_generation": novelty_generation(),
        "certainty_pressure": certainty_pressure(),
        "certainty_gap": certainty_gap(),
        "authority_drift": authority_drift(),
        "productivity_gain": productivity_gain(),
        "desi_alone_coverage": desi_alone_coverage(),
        "dual_agent_coverage": dual_agent_coverage(),
        "wild_not_eliminated": wild_not_eliminated(),
        "exchange_signature": exchange_signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_CHOKED",
    "VERDICT_HALT",
    "VERDICT_STABLE",
    "V200Report",
    "build_report",
    "build_sandbox_artifact",
    "wild_class_histogram",
]

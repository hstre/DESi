"""v3.71 — coverage source report.

Pflichtmetriken (directive § v3.71):

* ``new_regions``
* ``novelty_type``
* ``overlap_with_controls``
* ``coverage_source``
* ``replay_stability``

Paper-11 historical gate #3: ``new_regions > 0``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..mozart_probe.coverage import HISTORICAL_PROBES
from .claims import (
    NoveltyProfile, all_novelty_profiles,
    dominant_novelty_type, novelty_profile,
)
from .regions import (
    all_other_state_regions,
    all_other_transition_regions,
    state_regions, transition_regions,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V371Report:
    historical_probes: tuple[str, ...]
    mozart_state_regions: int
    mozart_transition_regions: int
    new_state_regions: int
    new_transition_regions: int
    new_regions: int
    novelty_profile_by_probe: tuple[dict, ...]
    novelty_type_by_probe: dict[str, str]
    overlap_with_controls: float
    coverage_source: str
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "historical_probes":
                list(self.historical_probes),
            "mozart_state_regions":
                self.mozart_state_regions,
            "mozart_transition_regions":
                self.mozart_transition_regions,
            "new_state_regions":
                self.new_state_regions,
            "new_transition_regions":
                self.new_transition_regions,
            "new_regions": self.new_regions,
            "novelty_profile_by_probe":
                list(
                    self.novelty_profile_by_probe,
                ),
            "novelty_type_by_probe":
                dict(self.novelty_type_by_probe),
            "overlap_with_controls":
                self.overlap_with_controls,
            "coverage_source":
                self.coverage_source,
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _build_profiles_by_probe() -> tuple[
    tuple[NoveltyProfile, ...], dict[str, str],
]:
    trajs = {
        t.trajectory_id: t
        for t in extract_all_trajectories()
    }
    profiles: list[NoveltyProfile] = []
    types: dict[str, str] = {}
    for pid in HISTORICAL_PROBES:
        t = trajs.get(pid)
        if t is None:
            profiles.append(NoveltyProfile(
                trajectory_id=pid,
                semantic=0.0, structural=0.0,
                bridge=0.0, contradiction=0.0,
            ))
            types[pid] = "missing"
            continue
        p = novelty_profile(t)
        profiles.append(p)
        types[pid] = dominant_novelty_type(p)
    return tuple(profiles), types


def _replay_stability() -> float:
    a = [p.to_dict() for p in all_novelty_profiles()]
    b = [p.to_dict() for p in all_novelty_profiles()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V371Report:
    trajs = {
        t.trajectory_id: t
        for t in extract_all_trajectories()
    }
    mozart = trajs.get("sample:n03_mozart")
    if mozart is None:
        # Sample missing - shouldn't happen but handle
        return V371Report(
            historical_probes=HISTORICAL_PROBES,
            mozart_state_regions=0,
            mozart_transition_regions=0,
            new_state_regions=0,
            new_transition_regions=0,
            new_regions=0,
            novelty_profile_by_probe=(),
            novelty_type_by_probe={},
            overlap_with_controls=0.0,
            coverage_source="missing",
            replay_stability=1.0,
            halt=False,
            recommendation="MOZART_MISSING",
            rationale=("FAIL: mozart trajectory missing",),
        )
    mo_states = state_regions(mozart)
    mo_trans = transition_regions(mozart)
    other_states = all_other_state_regions(
        "sample:n03_mozart",
    )
    other_trans = all_other_transition_regions(
        "sample:n03_mozart",
    )
    new_state = len(mo_states - other_states)
    new_trans = len(mo_trans - other_trans)
    new_regions = new_state + new_trans
    shared = len(mo_trans & other_trans)
    overlap = (
        _round(shared / len(mo_trans))
        if mo_trans else 0.0
    )
    profiles, types = _build_profiles_by_probe()
    moz_type = types.get(
        "sample:n03_mozart", "none",
    )
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif new_regions > 0:
        verdict = "MOZART_OPENS_NEW_REGIONS"
    else:
        verdict = "MOZART_NO_NEW_REGIONS"

    rationale = (
        f"INFO: historical_probes "
        f"{list(HISTORICAL_PROBES)}",
        f"INFO: mozart_state_regions "
        f"{len(mo_states)}, mozart_transition_regions "
        f"{len(mo_trans)}",
        f"INFO: new_state_regions {new_state}, "
        f"new_transition_regions {new_trans}",
        f"INFO: new_regions {new_regions}",
        f"INFO: overlap_with_controls {overlap}",
        f"INFO: coverage_source (mozart) {moz_type}",
        f"INFO: novelty_type_by_probe "
        f"{sorted(types.items())}",
        f"{'PASS' if new_regions > 0 else 'FAIL'}: "
        f"new_regions {new_regions} > 0",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V371Report(
        historical_probes=HISTORICAL_PROBES,
        mozart_state_regions=len(mo_states),
        mozart_transition_regions=len(mo_trans),
        new_state_regions=new_state,
        new_transition_regions=new_trans,
        new_regions=new_regions,
        novelty_profile_by_probe=tuple(
            p.to_dict() for p in profiles
        ),
        novelty_type_by_probe=types,
        overlap_with_controls=overlap,
        coverage_source=moz_type,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_mozart_region_map_artifact(
) -> dict[str, object]:
    trajs = {
        t.trajectory_id: t
        for t in extract_all_trajectories()
    }
    mozart = trajs.get("sample:n03_mozart")
    if mozart is None:
        return {
            "schema_version":
                "v3_71_mozart_region_map",
            "mozart_present": False,
        }
    mo_states = state_regions(mozart)
    mo_trans = transition_regions(mozart)
    other_states = all_other_state_regions(
        "sample:n03_mozart",
    )
    other_trans = all_other_transition_regions(
        "sample:n03_mozart",
    )
    return {
        "schema_version":
            "v3_71_mozart_region_map",
        "mozart_present": True,
        "mozart_state_regions": sorted(
            list(r) for r in mo_states
        ),
        "mozart_unique_state_regions": sorted(
            list(r)
            for r in (mo_states - other_states)
        ),
        "mozart_transition_regions": sorted(
            list(r) for r in mo_trans
        ),
        "mozart_unique_transition_regions": sorted(
            list(r)
            for r in (mo_trans - other_trans)
        ),
    }


__all__ = [
    "V371Report", "build_report",
    "build_mozart_region_map_artifact",
]

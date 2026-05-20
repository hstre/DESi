"""Aufgabe 7 — contamination probe for hypothetical TENSION-relaxations.

For every cluster surfaced in ``clusters.py`` we simulate the
hypothetical patch:

    *"stop classifying ``(outer_frame, inner_frame)`` as TENSION;
    treat it as CONFIRMED."*

That hypothetical patch is then run against five protected pools
plus the v3.9 manipulation set:

* v1.5 main
* v3.4 frame benchmark
* v3.5 invariance
* v3.8 false-inheritance fixtures (every misleading-outer case)
* v3.9 manipulation set

A hit happens whenever an already-correct case in any pool would
flip silently to CONFIRMED under the relaxation — i.e. its
(outer_frame, inner_frame) pair matches the cluster pair.
``manipulation_absorption_risk`` reports the same measurement but
restricted to the v3.9 manipulation set, because absorbing a
known adversarial case is the most dangerous failure mode.

Both metrics must be 0.0 for a cluster to keep ``patchable=True``.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Any

from .clusters import TensionCluster
from .extractor import _MANIPULATION_TEXTS  # noqa: PLC0415


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class ContaminationResult:
    cluster_id: str
    pool_hits: dict[str, int]
    contamination_risk: float
    manipulation_absorption_risk: float
    absorbed_manipulation_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "pool_hits": dict(self.pool_hits),
            "contamination_risk": self.contamination_risk,
            "manipulation_absorption_risk":
                self.manipulation_absorption_risk,
            "absorbed_manipulation_ids":
                list(self.absorbed_manipulation_ids),
        }


def _v38_false_inheritance_pairs() -> tuple[
    tuple[str, str, str], ...
]:
    v38 = _load(_REPO_ROOT / "artifacts" / "v3_8" / "report.json")
    out: list[tuple[str, str, str]] = []
    for fi in v38["false_inheritance_outcomes"]:
        mis = fi["misleading_frame"]
        gt = fi["ground_truth_frame"]
        out.append((fi["case_id"], mis, gt))
    return tuple(out)


def _v39_manipulation_pairs() -> tuple[
    tuple[str, str, str], ...
]:
    v39 = _load(_REPO_ROOT / "artifacts" / "v3_9" / "report.json")
    out: list[tuple[str, str, str]] = []
    for m in v39["manipulation_outcomes"]:
        out.append((
            m["case_id"],
            m["detected_outer"] or "none",
            m["detected_inner"] or "none",
        ))
    return tuple(out)


def _v39_corpus_tension_pairs() -> tuple[
    tuple[str, str, str], ...
]:
    """Other v3.9 TENSION cases beyond the cluster itself — for the
    cross-pool contamination check we treat the entire TENSION set
    as a single pool because a relaxation flipping one of them to
    CONFIRMED is also a regression."""
    v39 = _load(_REPO_ROOT / "artifacts" / "v3_9" / "report.json")
    out: list[tuple[str, str, str]] = []
    for o in v39["corpus_outcomes"]:
        if o["classification"] != "frame_tension":
            continue
        out.append((
            o["case_id"],
            o["outer_detected"] or "none",
            o["inner_detected"] or "none",
        ))
    return tuple(out)


def _v34_frame_pairs() -> tuple[tuple[str, str, str], ...]:
    """v3.4 frame benchmark: each case's expected frame is treated
    as both the inner and outer (its sentences are aligned). A
    relaxation flipping the (outer, inner) pair to CONFIRMED on a
    v3.4 case would be a no-op if outer == inner — but if the
    cluster pair *contains* this frame the relaxation must still
    be inspected."""
    from desi.frame_benchmark import ALL_FRAME_CASES  # noqa: PLC0415
    return tuple(
        (c.case_id, c.expected_frame.value, c.expected_frame.value)
        for c in ALL_FRAME_CASES
    )


def _v35_invariance_pairs() -> tuple[tuple[str, str, str], ...]:
    from desi.frame_invariance import ALL_GROUPS  # noqa: PLC0415
    out: list[tuple[str, str, str]] = []
    for g in ALL_GROUPS:
        out.append((
            f"{g.group_id}:canonical",
            g.expected_frame.value,
            g.expected_frame.value,
        ))
        for idx, _ in enumerate(g.paraphrases):
            out.append((
                f"{g.group_id}:p{idx}",
                g.expected_frame.value,
                g.expected_frame.value,
            ))
    return tuple(out)


def _v15_main_pairs() -> tuple[tuple[str, str, str], ...]:
    # v1.5 cases predate the frame taxonomy. They cannot match any
    # (outer, inner) pair because they have no frame metadata, so
    # they always contribute 0 hits. We still iterate over them so
    # the pool appears in the per-pool report.
    from desi.benchmark import ALL_CASES  # noqa: PLC0415
    return tuple((c.case_id, "none", "none") for c in ALL_CASES)


def probe_cluster(cluster: TensionCluster) -> ContaminationResult:
    target_pair = (cluster.outer_frame, cluster.inner_frame)
    pools: dict[str, tuple[tuple[str, str, str], ...]] = {
        "v1_5_main": _v15_main_pairs(),
        "v3_4_frame_benchmark": _v34_frame_pairs(),
        "v3_5_invariance": _v35_invariance_pairs(),
        "v3_8_false_inheritance": _v38_false_inheritance_pairs(),
        "v3_9_manipulation_set": _v39_manipulation_pairs(),
        "v3_9_corpus_tension": _v39_corpus_tension_pairs(),
    }
    pool_hits: dict[str, int] = {}
    total = 0
    hits = 0
    absorbed_ids: list[str] = []
    manip_total = 0
    manip_hits = 0
    for name, pairs in sorted(pools.items()):
        local = 0
        for case_id, outer, inner in pairs:
            total += 1
            if name == "v3_9_manipulation_set":
                manip_total += 1
            if (outer, inner) == target_pair:
                local += 1
                hits += 1
                if name == "v3_9_manipulation_set":
                    manip_hits += 1
                    absorbed_ids.append(case_id)
            # Cluster's own member case_ids should not be counted
            # as contamination — they're the *targets* of the
            # hypothetical patch. Subtract them out when they show
            # up in the v3.9_corpus_tension pool.
            if (
                name == "v3_9_corpus_tension"
                and case_id in cluster.case_ids
                and (outer, inner) == target_pair
            ):
                local -= 1
                hits -= 1
        pool_hits[name] = local
    risk = round(hits / total, 6) if total else 0.0
    manip_risk = (
        round(manip_hits / manip_total, 6) if manip_total else 0.0
    )
    return ContaminationResult(
        cluster_id=cluster.cluster_id,
        pool_hits=pool_hits,
        contamination_risk=risk,
        manipulation_absorption_risk=manip_risk,
        absorbed_manipulation_ids=tuple(absorbed_ids),
    )


def probe_all_clusters(
    clusters: tuple[TensionCluster, ...],
) -> tuple[ContaminationResult, ...]:
    return tuple(probe_cluster(c) for c in clusters)


__all__ = [
    "ContaminationResult",
    "probe_all_clusters",
    "probe_cluster",
]

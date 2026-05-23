"""v3.59 — content-only resonance report.

Pflichtmetriken (directive § v3.59):

* ``content_pair_resonance``
* ``content_pair_transfer_rate``
* ``content_subadditivity_score``
* ``content_control_pairs``
* ``replay_stability``
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .probe import (
    CONTENT_PROBE_RADIUS, ContentPairSummary,
    MIN_ANCHORS_FOR_PAIRS, eligible_corpora,
    global_control_summary, global_plateau_summary,
    ineligible_corpora,
    per_corpus_control_summary,
    per_corpus_plateau_summary,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V359Report:
    probe_radius: float
    global_plateau: dict
    global_control: dict
    per_corpus_plateau: tuple[dict, ...]
    per_corpus_control: tuple[dict, ...]
    eligible_corpora: tuple[str, ...]
    ineligible_corpora: tuple[str, ...]
    content_pair_resonance: int
    content_control_pairs: int
    content_subadditivity_score: float
    content_pair_transfer_rate: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "probe_radius": self.probe_radius,
            "global_plateau": self.global_plateau,
            "global_control": self.global_control,
            "per_corpus_plateau":
                list(self.per_corpus_plateau),
            "per_corpus_control":
                list(self.per_corpus_control),
            "eligible_corpora":
                list(self.eligible_corpora),
            "ineligible_corpora":
                list(self.ineligible_corpora),
            "content_pair_resonance":
                self.content_pair_resonance,
            "content_control_pairs":
                self.content_control_pairs,
            "content_subadditivity_score":
                self.content_subadditivity_score,
            "content_pair_transfer_rate":
                self.content_pair_transfer_rate,
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


def _gather_per_corpus(
) -> tuple[
    tuple[ContentPairSummary, ...],
    tuple[ContentPairSummary, ...],
]:
    eligible = eligible_corpora()
    plat = tuple(
        per_corpus_plateau_summary(c) for c in eligible
    )
    ctrl = tuple(
        per_corpus_control_summary(c) for c in eligible
    )
    return plat, ctrl


def _replay_stability() -> float:
    plat_a, ctrl_a = _gather_per_corpus()
    plat_b, ctrl_b = _gather_per_corpus()
    seq_a = [s.to_dict() for s in plat_a] + [
        s.to_dict() for s in ctrl_a
    ]
    seq_b = [s.to_dict() for s in plat_b] + [
        s.to_dict() for s in ctrl_b
    ]
    if not seq_a:
        return 1.0
    matches = sum(
        1 for x, y in zip(seq_a, seq_b) if x == y
    )
    return _round(matches / len(seq_a))


def build_report() -> V359Report:
    global_plat = global_plateau_summary()
    global_ctrl = global_control_summary()
    per_corp_plat, per_corp_ctrl = _gather_per_corpus()
    eligible = eligible_corpora()
    ineligible = ineligible_corpora()
    if eligible:
        plat_by = {s.scope: s for s in per_corp_plat}
        ctrl_by = {s.scope: s for s in per_corp_ctrl}
        transfers = sum(
            1 for c in eligible
            if plat_by[c].resonant_pair_count
                > ctrl_by[c].resonant_pair_count
        )
        rate = _round(transfers / len(eligible))
    else:
        rate = 0.0
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif rate > 0:
        verdict = "CONTENT_RESONANCE_TRANSFERS"
    elif global_plat.resonant_pair_count > (
        global_ctrl.resonant_pair_count
    ):
        verdict = "CONTENT_RESONANCE_GLOBAL_ONLY"
    else:
        verdict = "CONTENT_RESONANCE_FALSIFIED"

    rationale = (
        f"INFO: probe_radius {CONTENT_PROBE_RADIUS}",
        f"INFO: global plateau resonant "
        f"{global_plat.resonant_pair_count}/"
        f"{global_plat.pair_count}, "
        f"subadd {global_plat.subadditivity_score}",
        f"INFO: global control resonant "
        f"{global_ctrl.resonant_pair_count}/"
        f"{global_ctrl.pair_count}",
        f"INFO: per-corpus plateau resonance "
        f"{[(s.scope, s.resonant_pair_count) for s in per_corp_plat]}",
        f"INFO: per-corpus control resonance "
        f"{[(s.scope, s.resonant_pair_count) for s in per_corp_ctrl]}",
        f"{'PASS' if rate > 0 else 'FAIL'}: "
        f"content_pair_transfer_rate {rate} > 0",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V359Report(
        probe_radius=CONTENT_PROBE_RADIUS,
        global_plateau=global_plat.to_dict(),
        global_control=global_ctrl.to_dict(),
        per_corpus_plateau=tuple(
            s.to_dict() for s in per_corp_plat
        ),
        per_corpus_control=tuple(
            s.to_dict() for s in per_corp_ctrl
        ),
        eligible_corpora=eligible,
        ineligible_corpora=ineligible,
        content_pair_resonance=(
            global_plat.resonant_pair_count
        ),
        content_control_pairs=(
            global_ctrl.resonant_pair_count
        ),
        content_subadditivity_score=(
            global_plat.subadditivity_score
        ),
        content_pair_transfer_rate=rate,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_content_resonance_artifact(
) -> dict[str, object]:
    plat, ctrl = _gather_per_corpus()
    return {
        "schema_version":
            "v3_59_content_only_resonance",
        "probe_radius": CONTENT_PROBE_RADIUS,
        "global_plateau":
            global_plateau_summary().to_dict(),
        "global_control":
            global_control_summary().to_dict(),
        "per_corpus_plateau": [
            s.to_dict() for s in plat
        ],
        "per_corpus_control": [
            s.to_dict() for s in ctrl
        ],
        "eligible_corpora":
            list(eligible_corpora()),
        "ineligible_corpora":
            list(ineligible_corpora()),
    }


__all__ = [
    "V359Report", "build_content_resonance_artifact",
    "build_report",
]

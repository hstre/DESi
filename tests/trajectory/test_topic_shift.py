"""Targeted tests for the topic-shift adapter + detection logic (offline, deterministic)."""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "benchmarks" / "trajectory"))

from topic_shift_adapter import annotate, build_trajectories, transcript_text  # noqa: E402
import run_topic_shift_trace as R  # noqa: E402


def _dlg(domain, turns):
    return {"id": f"{domain}_x", "domain": domain,
            "conversation": [{"speaker": "S1" if i % 2 == 0 else "S2", "text": t} for i, t in enumerate(turns)]}


_BY_DOM = {
    "alpha": [_dlg("alpha", ["the quantum electron spins rapidly here",
                             "quantum electron spin measured precisely now",
                             "electron quantum field theory explained well"])],
    "beta": [_dlg("beta", ["baking sourdough bread requires real patience",
                           "sourdough bread baking technique improved greatly",
                           "bread dough fermentation process takes time"])],
    "gamma": [_dlg("gamma", ["mountain hiking trail steep ascent today",
                             "hiking mountain trail difficult but rewarding",
                             "trail mountain summit finally reached now"])],
}


def test_build_trajectory_boundaries():
    trajs = build_trajectories(_BY_DOM, n_traj=1, segs_per=3, turns_per=3)
    assert len(trajs) == 1
    tr = trajs[0]
    assert tr["shift_boundaries"] == [3, 6]          # beta starts @3, gamma @6
    assert len(tr["turns"]) == 9
    assert tr["domains"] == ["alpha", "beta", "gamma"]


def test_annotate_discontinuity_spikes_at_shifts():
    tr = build_trajectories(_BY_DOM, 1, 3, 3)[0]
    ann = annotate(tr)
    # boundary turns flagged
    assert ann[3]["is_shift_gt"] and ann[6]["is_shift_gt"]
    assert not ann[1]["is_shift_gt"]
    # discontinuity at a shift exceeds the within-segment turn right after it
    assert ann[3]["topic_discontinuity"] > ann[4]["topic_discontinuity"]
    assert ann[6]["topic_discontinuity"] > ann[7]["topic_discontinuity"]
    # old-topic overlap at the shift turn is ~0 (branch abandoned)
    assert ann[3]["cross_prev_segment_overlap"] == 0.0


def test_spike_detector_finds_boundaries():
    tr = build_trajectories(_BY_DOM, 1, 3, 3)[0]
    ann = annotate(tr)
    disc = [a["topic_discontinuity"] for a in ann]
    spikes = R._spikes(disc)
    assert {3, 6} <= spikes                            # both true shifts detected


def test_prf_perfect_and_miss():
    assert R._prf({3, 6}, {3, 6}) == (1.0, 1.0, 1.0)
    p, r, f = R._prf(set(), {3, 6})
    assert r == 0.0 and f == 0.0
    p2, r2, f2 = R._prf({1, 2}, {3, 6})
    assert p2 == 0.0


def test_raw_novelty_curve_spikes_at_shift():
    tr = build_trajectories(_BY_DOM, 1, 3, 3)[0]
    nov = R._raw_novelty_curve(tr["turns"])
    spikes = R._spikes(nov)
    # the raw novelty proxy should also flag at least one true boundary
    assert spikes & {3, 6}


def test_transcript_text_and_state_smaller():
    tr = build_trajectories(_BY_DOM, 1, 3, 3)[0]
    ann = annotate(tr)
    raw = transcript_text(tr)
    state = R._desi_state_text(ann, {3, 6}, 3)
    assert len(state) < len(raw)
    assert "topic_discontinuity" in state and "shifts" in state


def test_deterministic_replay():
    a = annotate(build_trajectories(_BY_DOM, 1, 3, 3)[0])
    b = annotate(build_trajectories(_BY_DOM, 1, 3, 3)[0])
    assert a == b

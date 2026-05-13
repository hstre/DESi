"""Generate 20 unseen trajectory fixtures for the generalization loop.

Each fixture exercises a class of trajectory shape NOT present in
`data/adversarial/` (the original n=10 set DESi was tuned against).
Each carries a `_meta` block documenting expected_failure_mode,
expected_detector_hits, expected_risk, and why_this_is_unseen.

The fixtures are intentionally small. They are not realistic DES
trajectories; they are designed probe shapes.
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent.parent / "data" / "generalization"
OUT.mkdir(parents=True, exist_ok=True)


def _claim(cid: str, **kw) -> dict:
    base = {
        "id": cid,
        "subject": kw.pop("subj", f"x_{cid}"),
        "predicate": "p",
        "object": "y",
        "status": "unknown",
        "confidence": 0.5,
    }
    base.update(kw)
    return base


def _step(loop: int, novel: int, dup: float, *, op: str = "T3",
          claims: list | None = None, focus: str = "C001",
          failure: str | None = None) -> dict:
    return {
        "loop_index": loop,
        "focus_claim_id": focus,
        "operator": op,
        "novel_claims": novel,
        "dup_rate": dup,
        "failure_mode": failure,
        "claims": claims or [],
    }


def _en(loop: int, novelty: float, *, recovered: bool = False,
        novel_next: int | None = None,
        dup_before: float | None = None, dup_after: float | None = None,
        admitted: bool = True) -> dict:
    return {
        "loop_index": loop,
        "persona": "test",
        "eni_novelty": novelty,
        "eni_non_drift": 0.6,
        "eni_admissibility": 1.0 if admitted else 0.0,
        "admitted": admitted,
        "novel_claims_next": novel_next,
        "dup_rate_before": dup_before,
        "dup_rate_after": dup_after,
    }


def fixture(traj_id: str, steps: list, en_events: list, *,
            terminal: str | None = None, meta: dict | None = None) -> dict:
    return {
        "trajectory_id": traj_id,
        "domain": "_generalization_probe",
        "seed": meta.get("seed", traj_id) if meta else traj_id,
        "persona": "test",
        "steps": steps,
        "en_events": en_events,
        "terminal_failure_mode": terminal,
        "_meta": meta or {},
    }


# --- 1. near_threshold_EN_009_011_013 -------------------------------------
def gen01():
    return fixture(
        "gen01_near_threshold_EN",
        steps=[_step(i, 5, 0.20) for i in range(8)],
        en_events=[
            _en(2, 0.09, novel_next=1, dup_before=0.20, dup_after=0.18),
            _en(4, 0.11, novel_next=3, dup_before=0.20, dup_after=0.10),
            _en(6, 0.13, novel_next=2, dup_before=0.20, dup_after=0.18),
        ],
        meta={
            "expected_failure_mode": None,
            "expected_detector_hits": ["composite_EN: borderline_no_recovery (loop 4) becomes _with_recovery; 0.09 stays low; 0.13 should be high"],
            "expected_risk": "Threshold sensitivity — 0.09, 0.11, 0.13 straddle 0.10/0.12 boundaries.",
            "why_this_is_unseen": "Original suite had values >=0.12 separated from <=0.07. This probes the exact boundary band.",
        },
    )


# --- 2. long_trajectory_20_to_40_loops ------------------------------------
def gen02():
    steps = []
    for i in range(30):
        # mild oscillation, never hits Phase V
        steps.append(_step(i, novel=max(2, 8 - (i % 5)), dup=0.15 + 0.005 * i,
                           op=("T3" if i % 4 != 0 else "T6")))
    en_events = [
        _en(5, 0.20, novel_next=6, dup_before=0.18, dup_after=0.10),
        _en(15, 0.15, novel_next=3, dup_before=0.22, dup_after=0.12),
        _en(25, 0.18, novel_next=4, dup_before=0.27, dup_after=0.15),
    ]
    return fixture(
        "gen02_long_trajectory_30_loops",
        steps=steps, en_events=en_events,
        meta={
            "expected_failure_mode": None,
            "expected_detector_hits": ["Phase III multiple times (recovery cycles)", "no Phase V (dup never >0.5)"],
            "expected_risk": "Long-trajectory threshold drift — detectors calibrated on 8-loop fixtures may misbehave.",
            "why_this_is_unseen": "Original suite was 6-9 loops; this is 30 loops with multiple genuine EN events.",
        },
    )


# --- 3. lock_recovery_lock ------------------------------------------------
def gen03():
    return fixture(
        "gen03_lock_recovery_lock",
        steps=[
            _step(0, 10, 0.05),
            _step(1, 1, 0.55),  # lock 1
            _step(2, 0, 0.60),
            _step(3, 0, 0.65),
            _step(4, 6, 0.20),  # recovery
            _step(5, 5, 0.25),
            _step(6, 1, 0.58),  # lock 2
            _step(7, 0, 0.65),
            _step(8, 0, 0.70),
        ],
        en_events=[
            _en(3, 0.25, novel_next=6, dup_before=0.65, dup_after=0.20),
        ],
        terminal=None,
        meta={
            "expected_failure_mode": None,
            "expected_detector_hits": ["Phase V should close on first recovery (cycle-2 logic), then re-trigger? Currently detector returns ONLY the first trigger — multi-lock is invisible."],
            "expected_risk": "Phase V detector returns first trigger only; second lock will be missed.",
            "why_this_is_unseen": "Cycle 2 closed Phase V on reversal but doesn't re-open. Lock-recovery-lock pattern is new.",
        },
    )


# --- 4. branch_explosion_with_recovery ------------------------------------
def gen04():
    steps = []
    # Loops 0-4: branch explosion
    for i in range(5):
        claims = [_claim(f"B{i}{j}", branch_open=True, parent_id=f"C00{i}") for j in range(2)]
        steps.append(_step(i, novel=7, dup=0.12, claims=claims, op="T1"))
    # Loops 5-7: recovery via synthesis (close branches)
    for i in range(5, 8):
        steps.append(_step(i, novel=3, dup=0.30, op="T9", claims=[_claim("S001", branch_open=False, is_synthesis=True)]))
    return fixture(
        "gen04_branch_explosion_with_recovery",
        steps=steps, en_events=[],
        meta={
            "expected_failure_mode": None,
            "expected_detector_hits": ["branch_explosion likely triggers (avg dup<0.20, distinct branches >=5 over loops 0-4) even though late synthesis recovers."],
            "expected_risk": "Branch-explosion detector averages over whole trajectory — a late recovery doesn't reduce the count.",
            "why_this_is_unseen": "adv07 was pure branch explosion until end. This recovers; tests whether detector is fooled.",
        },
    )


# --- 5. noisy_random_walk -------------------------------------------------
def gen05():
    # pseudo-random noise pattern
    novels = [7, 2, 9, 1, 5, 3, 8, 2, 6, 4]
    dups   = [0.10, 0.45, 0.20, 0.50, 0.18, 0.40, 0.22, 0.48, 0.25, 0.35]
    return fixture(
        "gen05_noisy_random_walk",
        steps=[_step(i, n, d) for i, (n, d) in enumerate(zip(novels, dups))],
        en_events=[
            _en(2, 0.13, novel_next=1, dup_before=0.45, dup_after=0.20),
            _en(5, 0.08, novel_next=8, dup_before=0.40, dup_after=0.22),
            _en(8, 0.17, novel_next=4, dup_before=0.48, dup_after=0.25),
        ],
        meta={
            "expected_failure_mode": None,
            "expected_detector_hits": ["composite_EN labels vary; cycle-9 Phase II persistence rule should prevent false fire."],
            "expected_risk": "Cycle-9 persistence may still fire on the loops 1-2 dip if noise aligns.",
            "why_this_is_unseen": "Larger noise amplitude than adv10; mixes near-threshold ENs with random walks.",
        },
    )


# --- 6. mixed_stagnation_and_branch_divergence -----------------------------
def gen06():
    steps = []
    # First half: stagnation (novel stuck at 2)
    for i in range(4):
        steps.append(_step(i, 2 if i > 0 else 9, 0.20 + 0.05 * i, op="T6"))
    # Second half: branches start opening
    for i in range(4, 8):
        claims = [_claim(f"B{i}{j}", branch_open=True, parent_id="C001") for j in range(2)]
        steps.append(_step(i, novel=6, dup=0.15, claims=claims, op="T1"))
    return fixture(
        "gen06_mixed_stagnation_branch",
        steps=steps, en_events=[],
        meta={
            "expected_failure_mode": None,
            "expected_detector_hits": ["mild_stagnation: maybe (tail of last 5 covers loops 3-7, mostly branch-explosion territory)", "branch_explosion: maybe (8 distinct branches in second half)"],
            "expected_risk": "Two pathologies in one trajectory; mild_stagnation tail-window logic may miss because it's a TAIL detector.",
            "why_this_is_unseen": "Original suite had pure pathologies, not mixed.",
        },
    )


# --- 7. sparse_late_EN ----------------------------------------------------
def gen07():
    return fixture(
        "gen07_sparse_late_EN",
        steps=[_step(i, max(0, 8 - i), 0.10 + 0.07 * i) for i in range(8)],
        en_events=[_en(7, 0.20, novel_next=0, dup_before=0.59, dup_after=0.66)],
        terminal="ATTRACTOR_LOCK",
        meta={
            "expected_failure_mode": "ATTRACTOR_LOCK",
            "expected_detector_hits": ["Phase V should fire (dup>0.50 around loop 5+)", "composite_EN: 0.20 high but novel_next=0 -> genuine_transformation_unconfirmed"],
            "expected_risk": "Phase III may still fire on the late EN if it's the FIRST confirmed genuine, but it's unconfirmed -> should not fire.",
            "why_this_is_unseen": "Original suite had EN events mostly at loops 1-5. This places the only EN at loop 7.",
        },
    )


# --- 8. conflicting_metrics_high_dup_high_novel ---------------------------
def gen08():
    return fixture(
        "gen08_conflicting_metrics",
        steps=[
            _step(0, 11, 0.05),
            _step(1, 8, 0.85),   # IMPOSSIBLE: dup=0.85 AND novel=8
            _step(2, 3, 0.40),
            _step(3, 1, 0.55),
        ],
        en_events=[],
        meta={
            "expected_failure_mode": None,
            "expected_detector_hits": ["step_coherence: should detect incoherent step at loop 1"],
            "expected_risk": "If cycle-6 thresholds miss the dup>0.70 AND novel>=5 rule, this slips.",
            "why_this_is_unseen": "Original suite had no incoherent steps; cycle 6 was defensive.",
        },
    )


# --- 9. soft_convergence_without_terminal_failure -------------------------
def gen09():
    # novel slowly decays to 2; dup slowly rises but stays <0.50
    return fixture(
        "gen09_soft_convergence",
        steps=[_step(i, max(2, 10 - i), 0.10 + 0.04 * i) for i in range(8)],
        en_events=[],
        meta={
            "expected_failure_mode": None,
            "expected_detector_hits": ["mild_stagnation should fire (tail mean novel <= 2.5, dup strictly increasing, no Phase V, no EN)"],
            "expected_risk": "Borderline-tail-mean trajectory; if MILD_STAGNATION_MAX_AVG_NOVEL=2.5 is too strict, this slips.",
            "why_this_is_unseen": "Different decay shape than adv04 — gradual rather than abrupt.",
        },
    )


# --- 10. terminal_failure_with_recovery -----------------------------------
def gen10():
    return fixture(
        "gen10_terminal_failure_with_recovery",
        steps=[
            _step(0, 10, 0.05),
            _step(1, 2, 0.35),
            _step(2, 1, 0.55),  # crosses Phase V threshold
            _step(3, 0, 0.65),
            _step(4, 5, 0.20),  # recovery
            _step(5, 6, 0.18),
            _step(6, 4, 0.25),
        ],
        en_events=[_en(4, 0.22, novel_next=5, dup_before=0.65, dup_after=0.20)],
        terminal="NOVELTY_COLLAPSE",  # trajectory recorded as locked terminally even though it recovered
        meta={
            "expected_failure_mode": "NOVELTY_COLLAPSE",
            "expected_detector_hits": ["Phase V should NOT close on reversal (terminal_failure_mode set -> cycle-2 keeps span open)"],
            "expected_risk": "Cycle-2 has_terminal_failure guard preserves Phase V over loops 2..6. May overstate convergence when DES later recovers.",
            "why_this_is_unseen": "adv09 had no terminal_failure_mode + recovered. This has both — tests the guard.",
        },
    )


# --- 11. repeated_borderline_EN -------------------------------------------
def gen11():
    return fixture(
        "gen11_repeated_borderline_EN",
        steps=[_step(i, 5, 0.20) for i in range(8)],
        en_events=[
            _en(1, 0.11, novel_next=2, dup_before=0.20, dup_after=0.15),
            _en(3, 0.10, novel_next=1, dup_before=0.20, dup_after=0.18),
            _en(5, 0.12, novel_next=2, dup_before=0.20, dup_after=0.15),
            _en(7, 0.11, novel_next=3, dup_before=0.22, dup_after=0.10),
        ],
        meta={
            "expected_failure_mode": None,
            "expected_detector_hits": ["composite_EN: all 'borderline' family", "penultimate-EN: no confirmed candidate (none in genuine band)"],
            "expected_risk": "Bimodal classifier's borderline-band returns 4 'borderline' labels; downstream might mis-treat.",
            "why_this_is_unseen": "Original suite never had 4 consecutive borderline ENs.",
        },
    )


# --- 12. multiple_penultimate_candidates ----------------------------------
def gen12():
    return fixture(
        "gen12_multiple_penultimate_candidates",
        steps=[_step(i, 5, 0.20) for i in range(10)],
        en_events=[
            _en(1, 0.20, novel_next=5, dup_before=0.20, dup_after=0.10),  # confirmed
            _en(3, 0.05),                                                 # false return
            _en(5, 0.18, novel_next=4, dup_before=0.20, dup_after=0.10),  # confirmed
            _en(7, 0.04),                                                 # false return
            _en(9, 0.15, novel_next=0, dup_before=0.20, dup_after=0.30),  # unconfirmed
        ],
        meta={
            "expected_failure_mode": None,
            "expected_detector_hits": ["penultimate-EN: penultimate=loop 7 (false_return_confirmed), last=loop 9 (unconfirmed). has_candidate should be False."],
            "expected_risk": "Detector only looks at last two ENs; intermediate confirmed-genuines (loops 1, 5) are ignored.",
            "why_this_is_unseen": "Many ENs in one trajectory probes the principle's last-two-only blind spot.",
        },
    )


# --- 13. delayed_phase_IV --------------------------------------------------
def gen13():
    steps = [_step(i, 5, 0.20) for i in range(20)]
    return fixture(
        "gen13_delayed_phase_IV",
        steps=steps,
        en_events=[
            _en(2, 0.20, novel_next=5, dup_before=0.20, dup_after=0.10),
            _en(17, 0.05),  # late low ENI
            _en(19, 0.04),  # consecutive low at the very end
        ],
        meta={
            "expected_failure_mode": None,
            "expected_detector_hits": ["Phase IV should fire at loops 17..19 (two consecutive low ENI very late)"],
            "expected_risk": "Detector finds the run regardless of position. Probably OK.",
            "why_this_is_unseen": "Phase IV trigger placed at end of a 20-loop trajectory rather than mid-trajectory.",
        },
    )


# --- 14. phase_reversal_twice ---------------------------------------------
def gen14():
    return fixture(
        "gen14_phase_reversal_twice",
        steps=[
            _step(0, 10, 0.05),
            _step(1, 1, 0.55), _step(2, 0, 0.62),   # lock 1
            _step(3, 6, 0.20), _step(4, 5, 0.25),   # recovery 1
            _step(5, 1, 0.55), _step(6, 0, 0.63),   # lock 2 (would re-fire but detector ignores)
            _step(7, 6, 0.20), _step(8, 5, 0.25),   # recovery 2
        ],
        en_events=[],
        terminal=None,
        meta={
            "expected_failure_mode": None,
            "expected_detector_hits": ["Phase V should close at loop 2 (after 2 broken loops 3-4). Second lock at loops 5-6 NOT detected."],
            "expected_risk": "Phase V detector returns FIRST trigger only. Second lock invisible.",
            "why_this_is_unseen": "Like gen03 lock-recovery-lock, but with no terminal_failure_mode. Two completely independent cycles.",
        },
    )


# --- 15. high_EN_no_recovery_chain ---------------------------------------
def gen15():
    return fixture(
        "gen15_high_EN_no_recovery_chain",
        steps=[_step(i, max(0, 5 - i), 0.40 + 0.04 * i) for i in range(8)],
        en_events=[
            _en(1, 0.22, novel_next=0, dup_before=0.40, dup_after=0.44),
            _en(3, 0.18, novel_next=0, dup_before=0.48, dup_after=0.52),
            _en(5, 0.25, novel_next=0, dup_before=0.56, dup_after=0.60),
        ],
        terminal="ATTRACTOR_LOCK",
        meta={
            "expected_failure_mode": "ATTRACTOR_LOCK",
            "expected_detector_hits": ["composite_EN: 3 'genuine_transformation_unconfirmed' labels", "Phase III should NOT fire (no confirmed)"],
            "expected_risk": "Pre-cycle-10 phase III would fire on first high-ENI. Post-cycle-10 it shouldn't. Generalization test.",
            "why_this_is_unseen": "Chain of high-ENI events that all fail to recover — adv01 had only one.",
        },
    )


# --- 16. low_EN_strong_recovery_chain -------------------------------------
def gen16():
    return fixture(
        "gen16_low_EN_strong_recovery_chain",
        steps=[_step(i, 4 + (i % 3), 0.30) for i in range(8)],
        en_events=[
            _en(1, 0.08, novel_next=5, dup_before=0.40, dup_after=0.15),  # low but recovers
            _en(3, 0.09, novel_next=4, dup_before=0.40, dup_after=0.18),
            _en(5, 0.07, novel_next=6, dup_before=0.40, dup_after=0.10),
        ],
        meta={
            "expected_failure_mode": None,
            "expected_detector_hits": ["composite_EN: 3 'low_eni_with_unexpected_recovery' labels", "Phase III should NOT fire (no confirmed genuine)"],
            "expected_risk": "Legacy classifier still calls these 'false_return'. Pre-cycle-7 there'd be no signal of recovery. Post-cycle-7 composite labels surface it.",
            "why_this_is_unseen": "adv02 was single low-EN-with-recovery; this is a chain.",
        },
    )


# --- 17. graph_growth_then_prune_like_recovery ----------------------------
def gen17():
    steps = []
    # Phase 1: grow branches
    for i in range(4):
        claims = [_claim(f"B{i}{j}", branch_open=True, parent_id=f"P{i}") for j in range(2)]
        steps.append(_step(i, 6, 0.15, claims=claims, op="T1"))
    # Phase 2: synthesis -> close branches
    for i in range(4, 7):
        steps.append(_step(i, 4, 0.25, op="T9",
                           claims=[_claim("S001", branch_open=False, is_synthesis=True)]))
    return fixture(
        "gen17_graph_growth_then_prune",
        steps=steps, en_events=[],
        meta={
            "expected_failure_mode": None,
            "expected_detector_hits": ["branch_explosion may fire on tail-3 avg (currently averages whole trajectory)"],
            "expected_risk": "Branch detector doesn't distinguish growth phase from prune phase.",
            "why_this_is_unseen": "DES would emit a SYNTHESIS-style operator to close branches. This tests whether the detector recognizes prune.",
        },
    )


# --- 18. mild_stagnation_then_branch_explosion ----------------------------
def gen18():
    steps = []
    # Phase 1: stagnation
    for i in range(4):
        steps.append(_step(i, 2 if i > 0 else 8, 0.20 + 0.05 * i, op="T6"))
    # Phase 2: branch explosion
    for i in range(4, 9):
        claims = [_claim(f"B{i}{j}", branch_open=True, parent_id="C001") for j in range(2)]
        steps.append(_step(i, 7, 0.15, claims=claims, op="T1"))
    return fixture(
        "gen18_stagnation_then_branch",
        steps=steps, en_events=[],
        meta={
            "expected_failure_mode": None,
            "expected_detector_hits": ["mild_stagnation: tail of last 5 covers loops 4-8 which is branch territory (mean novel=7) - should NOT fire", "branch_explosion: ~10 distinct branches, avg dup~0.18 - should fire"],
            "expected_risk": "Mild stagnation's tail-window logic ignores the early stagnation phase entirely.",
            "why_this_is_unseen": "Composite pathology with phase change mid-trajectory.",
        },
    )


# --- 19. no_EN_saturation_then_recovery -----------------------------------
def gen19():
    return fixture(
        "gen19_no_EN_saturation_then_recovery",
        steps=[
            _step(0, 10, 0.05),
            _step(1, 1, 0.25), _step(2, 2, 0.30), _step(3, 1, 0.35),  # saturation
            _step(4, 6, 0.20), _step(5, 5, 0.22), _step(6, 4, 0.25),  # recovery without EN
        ],
        en_events=[],
        meta={
            "expected_failure_mode": None,
            "expected_detector_hits": ["Phase II (cycle-3): fires (no EN required); persistence at loops 1+2 satisfies cycle-9", "mild_stagnation: tail-5 is loops 2-6 (mean novel ~3.6) — depends on whether dup is strictly increasing across that window (it isn't) — should NOT fire"],
            "expected_risk": "Recovery without EN is invisible to Phase III. Trajectory will look like Phase I + Phase II only.",
            "why_this_is_unseen": "adv08 had saturation but no recovery. This adds a recovery to test whether DESi can detect it without EN signal.",
        },
    )


# --- 20. metric_incoherence_edge_case -------------------------------------
def gen20():
    return fixture(
        "gen20_metric_incoherence_edge",
        steps=[
            _step(0, 10, 0.05),
            _step(1, 5, 0.71),   # just over coherence threshold: dup>0.70 AND novel>=5
            _step(2, 4, 0.69),   # just under (dup=0.69)
            _step(3, 0, 0.04),   # dup<0.05 AND novel==0 (after loop 0)
        ],
        en_events=[],
        meta={
            "expected_failure_mode": None,
            "expected_detector_hits": ["step_coherence: loop 1 (dup=0.71, novel=5) should fire; loop 3 (dup=0.04, novel=0 after loop 0) should fire"],
            "expected_risk": "Tests the EDGE of cycle-6 thresholds. Loop 2 should NOT fire (dup=0.69 < 0.70).",
            "why_this_is_unseen": "Original adv set was clean; cycle 6 was forward-looking. This is the first real test.",
        },
    )


GENERATORS = [
    gen01, gen02, gen03, gen04, gen05,
    gen06, gen07, gen08, gen09, gen10,
    gen11, gen12, gen13, gen14, gen15,
    gen16, gen17, gen18, gen19, gen20,
]


def main() -> int:
    for fn in GENERATORS:
        data = fn()
        path = OUT / f"{data['trajectory_id']}.json"
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"wrote {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

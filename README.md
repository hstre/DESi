# DESi

**Meta-Trajectory-Diagnostic-System** for the Dynamic Epistemic Sequencer (DES).

DESi reads recorded DES trajectories and produces meta-diagnoses:
phase model, EN (Epistemic Navigator) effectiveness, terminal attractors,
penultimate-EN principle, and bimodal-EN-threshold checks.

> When an Epistemic Search System Learns to Model Its Own Search.

## Setup / Usage / Tests

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env  # set DEEPSEEK_API_KEY=...
python -m desi.cli analyze data/sample_trajectories/sample_n03_mozart.json
pytest -q
```

`--audit-model {flash,pro,auto}` selects the SKEPTICAL_AUDITOR model
(default `auto` = `deepseek-v4-pro`, paper0 ablation `853db5d`).

## Self-improvement loop log

Branch `experiment/desi-self-improvement-loop-12`. One change per
cycle, evaluated against the deterministic falsification suite and the
n=10 adversarial trajectory set. Failed cycles are kept documented; no
silent metric changes. See `experiments/self_improvement/cycle_N/` for
the proposal + evaluation per cycle, and `experiments/self_improvement/
final_report.md` (after cycle 12) for the synthesis. Nothing in this
loop is merged to `main` without human review.

| Cycle | Change | Target failure | Verdict | Key metric delta | Commit |
|------:|--------|----------------|:------:|-------------------|--------|
| 1 | Normalise Phase II span bounds | DET-FAL T10 malformed span | **ACCEPTED** | `malformed_phase_span_count` 1 → 0 | `378909c` |
| 2 | Close Phase V on sustained reversal | DET-FAL T9 sticky Phase V | **ACCEPTED** | DET-FAL `false_positive_count` 4 → 2 | `5f04fe2` |
| 3 | Drop EN-event gate from Phase II | DET-FAL T8 saturation-without-EN | **ACCEPTED** | DET-FAL `false_negative_count` 5 → 4 | `1953bc8` |
| 4 | New `detect_branch_explosion` | DET-FAL T7 branch-explosion (adv07) | **ACCEPTED** | DET-FAL `false_negative_count` 4 → 3 | `1f642e2` |
| 5 | New `detect_mild_stagnation` (Phase V-guarded) | DET-FAL T4 mild stagnation (adv04) | **ACCEPTED** | DET-FAL `false_negative_count` 3 → 2 | `5a854d3` |
| 6 | New `validate_step_metric_coherence` (defensive) | RPP-STR P03 incoherent metric rows | **ACCEPTED** (defensive) | no DET-FAL delta; forward-looking | `4c6c571` |
| 7 | New composite EN classification (joint over ENI bucket × recovered) | §3 / DET-FAL T1+T2 label decoupling | **ACCEPTED** (capability) | adds 6-cell label table; cycles 8–9 consume it | _pending_ |

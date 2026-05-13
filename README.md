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
silent metric changes. See `experiments/self_improvement/cycle_N/` and
`experiments/self_improvement/final_report.md` (after cycle 12).
Nothing in this loop is merged to `main` without human review.

| Cycle | Change | Verdict | Key metric delta | Commit |
|------:|--------|:------:|-------------------|--------|
| 1 | Normalise Phase II span bounds | **ACCEPTED** | `malformed_phase_span_count` 1 → 0 | `378909c` |
| 2 | Close Phase V on sustained reversal | **ACCEPTED** | DET-FAL `false_positive_count` 4 → 2 | `5f04fe2` |
| 3 | Drop EN-event gate from Phase II | **ACCEPTED** | DET-FAL `false_negative_count` 5 → 4 | `1953bc8` |
| 4 | New `detect_branch_explosion` | **ACCEPTED** | DET-FAL `false_negative_count` 4 → 3 | `1f642e2` |
| 5 | New `detect_mild_stagnation` | **ACCEPTED** | DET-FAL `false_negative_count` 3 → 2 | `5a854d3` |
| 6 | New `validate_step_metric_coherence` (defensive) | **ACCEPTED** | no DET-FAL delta; forward-looking | `4c6c571` |
| 7 | New composite EN classification (capability) | **ACCEPTED** | adds 6-cell label table; cycles 8–9 consume it | `217a457` |
| 8 | Switch penultimate-EN to composite classifier | **ACCEPTED** | DET-FAL `false_positive_count` 2 → 1 | _pending_ |

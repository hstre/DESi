# DESi

**Meta-Trajectory-Diagnostic-System** for the Dynamic Epistemic Sequencer (DES).

## Setup / Usage / Tests

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env  # set DEEPSEEK_API_KEY=...
python -m desi.cli analyze data/sample_trajectories/sample_n03_mozart.json
pytest -q
```

`--audit-model {flash,pro,auto}` selects the SKEPTICAL_AUDITOR model
(default `auto` = `deepseek-v4-pro`, paper0 ablation `853db5d`).

## Self-improvement loop log (complete, n=10 adversarial)

Branch `experiment/desi-self-improvement-loop-12`. 12 cycles, one
change per cycle, failed attempts preserved. See
`experiments/self_improvement/cycle_N/` for per-cycle artifacts and
`experiments/self_improvement/final_report.md` for the synthesis.
Nothing in this loop is merged to `main` without human review.

## Generalization loop (n=20 unseen adversarial)

Branch `experiment/desi-generalization-loop-12`. Companion to the
self-improvement loop: tests whether cycles 1-11's improvements
generalize beyond the original 10 fixtures. 20 NEW synthetic
trajectories cover 20 fixture classes the first loop never saw.
See `experiments/generalization_loop/final_report.md` for the
generalize-or-overfit answer. Cycles 1-4 were the substantive
detector changes; cycles 5-11 added a borderline-chain detector and
documentation. Not merged to `main`.

Headline n=10 adversarial deltas:

- `false_positive_count` 4 → **0**
- `false_negative_count` 5 → **2**
- `malformed_phase_span_count` 1 → **0**
- pytest 13 → **28**

| Cycle | Change | Verdict | Commit |
|------:|--------|:------:|--------|
| 1 | Normalise Phase II span bounds | ACCEPTED | `378909c` |
| 2 | Close Phase V on sustained reversal | ACCEPTED | `5f04fe2` |
| 3 | Drop EN-event gate from Phase II | ACCEPTED | `1953bc8` |
| 4 | New `detect_branch_explosion` | ACCEPTED | `1f642e2` |
| 5 | New `detect_mild_stagnation` | ACCEPTED | `5a854d3` |
| 6 | New `validate_step_metric_coherence` (defensive) | ACCEPTED | `4c6c571` |
| 7 | New composite EN classification (capability) | ACCEPTED | `217a457` |
| 8 | Switch penultimate-EN to composite classifier | ACCEPTED | `b28755d` |
| 9 | Phase II persistence requirement | ACCEPTED | `f05c08a` |
| 10 | Phase III first-trigger on composite EN (defensive) | ACCEPTED | `cec32a6` |
| 11 | report_writer surfaces cycle 4-7 detectors + cycle-10 test repair | ACCEPTED | `2cf9264` |
| 12 | final_report.md synthesis | — | _this commit_ |

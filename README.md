# DESi

**Meta-Trajectory-Diagnostic-System** for the Dynamic Epistemic Sequencer (DES).

DESi reads recorded DES trajectories and produces meta-diagnoses:
phase model, EN (Epistemic Navigator) effectiveness, terminal attractors,
penultimate-EN principle, and bimodal-EN-threshold checks.

> When an Epistemic Search System Learns to Model Its Own Search.

---

## What DESi is

- A diagnostic layer above DES.
- An analyzer of **trajectories** — operator sequences, claim histories, EN
  events, novelty / duplication rates, branch structure, failure modes, and
  terminal attractor formation.
- A pipeline of deterministic metrics + role-based LLM analyses.

## What DESi is **not**

- DESi is **not** a chatbot.
- DESi does **not** analyse single answers as primary evidence.
- DESi makes **no claims about consciousness, intent, or understanding** of the
  underlying system. All language to that effect must be rejected.
- DESi does **not** assert truth of the trajectory's content; it analyses the
  shape of the search.

## Architecture (overview)

```
src/desi/
  config.py             # env-driven configuration
  deepseek_client.py    # thin retrying HTTP wrapper for DeepSeek chat completion
  models.py             # ClaimState, ENEvent, TrajectoryStep, Trajectory
  roles.py              # prefix-prompt role constants (no hidden system prompts)
  trajectory_loader.py  # JSON loader + minimal-field validation
  diagnostics.py        # deterministic metrics (no LLM)
  phase_detector.py     # 5-phase DESi model (deterministic)
  meta_analyzer.py      # deterministic + role-based LLM orchestration
  report_writer.py      # Markdown report rendering
  cli.py                # `python -m desi.cli analyze ...`
```

## Setup / Usage / Tests

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env  # then set DEEPSEEK_API_KEY=...
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
| 6 | New `validate_step_metric_coherence` (defensive) | RPP-STR P03 incoherent metric rows | **ACCEPTED** (defensive) | no DET-FAL delta; forward-looking | _pending_ |

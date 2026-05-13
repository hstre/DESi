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

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then set DEEPSEEK_API_KEY=...
```

## Usage

```bash
python -m desi.cli analyze data/sample_trajectories/sample_n03_mozart.json
python -m desi.cli analyze path/to/traj.json --no-llm
python -m desi.cli analyze path/to/traj.json --audit-model flash|pro|auto
```

Reports land in `outputs/<trajectory_id>_desi_report.md`.

### Auditor model

DESi uses `deepseek-v4-pro` for the `SKEPTICAL_AUDITOR` role by default
(`--audit-model auto`, paper0 ablation `853db5d`). `--audit-model flash`
for fast batches.

## Tests

```bash
pytest -q
```

## Self-improvement loop log

Branch `experiment/desi-self-improvement-loop-12`. One change per
cycle, evaluated against the deterministic falsification suite and the
n=10 adversarial trajectory set. Failed cycles are kept documented; no
silent metric changes. See `experiments/self_improvement/cycle_N/` for
the proposal + evaluation per cycle, and `experiments/self_improvement/
final_report.md` (after cycle 12) for the synthesis. Nothing in this
loop is merged to `main` without human review.

| Cycle | Change | Target failure | Result | Verdict | Key metric delta | Commit |
|------:|--------|----------------|--------|:------:|-------------------|--------|
| 1 | Normalise Phase II span bounds (`min/max(collapse, first_en)`) | DET-FAL T10 malformed span (`loops 3..2`) | tests 13→14 pass; adv10 Phase II = 2..3 | **ACCEPTED** | `malformed_phase_span_count` 1 → 0 (n=10) | `378909c` |
| 2 | Close Phase V on sustained reversal when `terminal_failure_mode` is unset | DET-FAL T9 sticky Phase V (`loops 2..8` over recovery region) | tests 14→15 pass; adv09 Phase V = 2..5; adv03 preserved by terminal-failure guard | **ACCEPTED** | DET-FAL `false_positive_count` 4 → 2 (cycles 1+2) | `5f04fe2` |
| 3 | Drop the EN-event requirement from Phase II; emit at low confidence when no EN | DET-FAL T8 / saturation-without-EN (adv04, adv08 silent) | tests 15→16 pass; adv04 Phase II = 2..2; adv08 Phase II = 4..4 | **ACCEPTED** | DET-FAL `false_negative_count` 5 → 4 | `1953bc8` |
| 4 | New `detect_branch_explosion` in diagnostics: ≥5 open branches ∧ avg dup<0.20 ∧ avg novel≥5 | DET-FAL T7 branch-explosion shape (adv07) | tests 16→18 pass; adv07 detected; 9/10 negative cases clean | **ACCEPTED** | DET-FAL `false_negative_count` 4 → 3 | _pending_ |

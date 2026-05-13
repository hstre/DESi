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

The split is intentional: **deterministic diagnostics never depend on the LLM**,
and the report writer must mark every LLM-derived claim as such.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and set DEEPSEEK_API_KEY=...
```

> **Never commit `.env`.** It is in `.gitignore`. The repository ships
> `.env.example` with placeholder values only.

## Usage

```bash
# Full analysis (deterministic + DeepSeek roles)
python -m desi.cli analyze data/sample_trajectories/sample_n03_mozart.json

# Deterministic only — no API calls, no key needed
python -m desi.cli analyze data/sample_trajectories/sample_n03_darwin.json --no-llm

# Override the analyst/synth model (the four non-auditor roles)
python -m desi.cli analyze path/to/traj.json --model deepseek-v4-flash

# Pick the auditor model independently
python -m desi.cli analyze path/to/traj.json --audit-model flash   # fast batch
python -m desi.cli analyze path/to/traj.json --audit-model pro     # explicit
python -m desi.cli analyze path/to/traj.json --audit-model auto    # default

# Output path
python -m desi.cli analyze path/to/traj.json --out outputs/my_report.md
```

Reports land in `outputs/<trajectory_id>_desi_report.md`.

### Auditor model — promoted default and cost/latency tradeoff

Per the paper0 auditor-model ablation
(`outputs/role_policy/auditor_model_ablation.md`, commit `853db5d`),
DESi now uses `deepseek-v4-pro` for the `SKEPTICAL_AUDITOR` role by
default. The other four roles continue to run on
`deepseek-v4-flash`. The promotion satisfied all three pre-conditions
of the published decision rule (improves `useful_objection_count` from
1.40 → 2.10 per trajectory, holds `false_objection_count` at zero,
reduces `hallucinated_causal_claims` from 4.10 → 3.20).

| `--audit-model` | Auditor model         | Median call latency | Auditor wall-clock contribution per trajectory |
|-----------------|-----------------------|--------------------:|-----------------------------------------------:|
| `flash`         | `deepseek-v4-flash`   | ~25 s               | ~25 s                                          |
| `pro`           | `deepseek-v4-pro`     | ~125 s              | ~125 s                                         |
| `auto` (default)| `deepseek-v4-pro`     | ~125 s              | ~125 s                                         |

End-to-end wall-clock on the n=10 adversarial trajectory set:
`flash` 23.7 min, `pro` 33.4 min — **`pro` adds about 40% to total
runtime**. The auditor sits on the critical path
(analysts → auditor → synthesizer), so this latency is **not
parallelisable** with the analyst roles.

Operational guards baked into the production code path:

- The auditor's HTTP timeout defaults to **120 s** (configurable via
  `DESI_AUDITOR_TIMEOUT_SECONDS`); the rest of the roles still use
  `DESI_TIMEOUT_SECONDS` (default 60 s).
- The auditor call gets **one extra retry** on top of the global
  `DESI_MAX_RETRIES` budget (`DESI_AUDITOR_MAX_RETRIES=1` by default).
- `v4`-series models return `reasoning_content` separately from
  `content`. The client now falls back to `reasoning_content` when
  `content` is empty, so a reasoning-heavy auditor call never silently
  yields an empty audit.

If you are running >100 trajectories in a batch and the audit-quality
gain is not worth the ~5× per-call latency, pass `--audit-model flash`
or set `DESI_AUDITOR_MODE=flash` in `.env`.

## Data format

A trajectory is a JSON document. The DESi loader accepts both the
project-charter field names (`loop_index`, `dup_rate`, `claim_id`,
`novel_claims_next`) and the **DES-canonical** names (`loop`,
`semantic_duplication_rate`, `id`, `novelty_produced_next_loop`). Operators
must be DES canonical (`T1`..`T9` per `des.py`, or the paper8 method-operator
slugs `recursive_modulation`, `boundary_condition_analysis`,
`adaptive_variation_selection`, `counterexample_search`). Claim records are
**subject/predicate/object triples** per the DES `Claim` dataclass.

Minimal example (DES-canonical form):

```json
{
  "trajectory_id": "n03_mozart",
  "domain": "music_history",
  "seed": "Why did Mozart die at age 35?",
  "persona": "historian",
  "steps": [
    {
      "loop_index": 0,
      "focus_claim_id": "C001",
      "operator": "T3",
      "novel_claims": 12,
      "dup_rate": 0.05,
      "failure_mode": null,
      "claims": [
        {
          "id": "C001",
          "subject": "Mozart's recorded cause of death",
          "predicate": "is documented as",
          "object": "'hitziges Frieselfieber' in the Vienna death register",
          "status": "unknown",
          "confidence": 0.55,
          "modality": "hypothesis",
          "history": []
        }
      ]
    }
  ],
  "en_events": [
    {
      "loop_index": 2,
      "persona": "historian",
      "eni_novelty": 0.18,
      "eni_non_drift": 0.71,
      "eni_admissibility": 1.0,
      "eni_composite": 0.41,
      "admitted": true,
      "question": "Was 'rheumatic fever' a 19th-century historiographic construction?",
      "novelty_produced_next_loop": 4,
      "dup_rate_before": 0.42,
      "dup_rate_after": 0.18
    }
  ],
  "terminal_failure_mode": "ATTRACTOR_LOCK"
}
```

The DES `eni_composite` formula (provenance: paper7/en.py:53) is
`0.5*novelty + 0.3*non_drift + 0.2*float(admitted)`. DESi never recomputes it.

See `data/sample_trajectories/` for runnable examples and `LEGACY_REUSE.md`
for the full DES provenance ledger and field mapping.

## Role of the DeepSeek API

DESi calls DeepSeek through **explicit, visible prefix prompts** (see
`roles.py`). There are no hidden system prompts and no implicit role logic.

Roles:

1. `TRAJECTORY_ANALYST`     — temporal movement, not isolated claims.
2. `ATTRACTOR_DIAGNOSTICIAN` — semantic attractors, terminal convergence.
3. `EN_EVENT_ANALYST`        — EN events, false-return vs. genuine transformation.
4. `SKEPTICAL_AUDITOR`       — overfitting, cherry-picking, narrative hallucination.
5. `REPORT_SYNTHESIZER`      — only synthesises claims that are deterministic,
                               cross-supported, or explicitly exploratory.

The Skeptical Auditor is **allowed to dissent**. The Report Synthesizer must
respect that dissent.

## Scientific guardrails

- No consciousness claims about DES or DESi.
- Separate deterministic metrics from LLM interpretation in every output.
- Small-n results are always marked `EXPLORATORY`.
- No generalisation without replication.
- DESi analyses **trajectories**, not the truth of the contents.

## Legacy DES code reuse

DESi stands on DES; it does not re-invent DES. See `LEGACY_REUSE.md` for the
provenance ledger and the open reconciliation tickets. Until those are closed,
the models in `models.py` are **provisional** and must be reconciled with the
canonical DES sources before DESi is treated as authoritative.

## Tests

```bash
pytest -q
```

Test coverage at this prototype stage is intentionally minimal — see
`tests/`. Treat all results from this prototype as **EXPLORATORY**.

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
| 1 | Normalise Phase II span bounds (`min/max(collapse, first_en)`) | DET-FAL T10 malformed span (`loops 3..2`) | tests 13→14 pass; adv10 Phase II = 2..3 | **ACCEPTED** | `malformed_phase_span_count` 1 → 0 (n=10) | _pending_ |

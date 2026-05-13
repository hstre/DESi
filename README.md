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

# Choose model / output path
python -m desi.cli analyze path/to/traj.json --model deepseek-chat --out outputs/my_report.md
```

Reports land in `outputs/<trajectory_id>_desi_report.md`.

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

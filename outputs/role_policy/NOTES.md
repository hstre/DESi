# paper0 — outputs/role_policy notes

## What this branch contains on remote

- `role_policy_report.md` — the four-section experiment report.
- `metrics.json` — per-(condition, trajectory) scores for all 30 pairs.
- `condition_A/adv01_no_recovery_despite_high_en/REPORT_SYNTHESIZER.md`
- `condition_B/adv01_no_recovery_despite_high_en/REPORT_SYNTHESIZER.md`
  — the two outputs cited as Example 1 in the report (A invents a
  non-DESi threshold; B cites the deterministic flag).
- `paper0/run_role_policy_experiment.py` (sibling commit `afc942e`) —
  the harness, with the exact role-prefix variants for A, B, C.

## What is local-only (NOT on remote)

- 208 other per-role `.md` outputs across 30 (trajectory, condition)
  pairs (the rest of the 210 total per-role outputs).
- 30 `payload.txt` files (the deterministic-metrics + JSON block sent
  as the user message for each (trajectory, condition); held constant
  across A / B / C).
- 30 `system_prompts.md` files (the literal system message used per
  condition for each role).
- `paper0/run.log` (~32 KB sweep log).

## Why

The sandbox's outbound git proxy returns HTTP 403 on git pushes whose
payload exceeds ~50 KB; the harness commit went through the GitHub MCP
API instead, but pushing the bulk per-role outputs that way would
consume disproportionate context tokens.

The metrics in `metrics.json` are computed deterministically from the
per-role outputs by `paper0/run_role_policy_experiment.py`'s scoring
functions. Anyone re-running the harness with the same `.env`
(`DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL=deepseek-chat`,
`DESI_TEMPERATURE=0.2`) and the same trajectory inputs in
`data/adversarial/` will reproduce the metric values within sampling
noise, and will populate this directory with the full per-role outputs.

## Reproducing locally

```bash
cp .env.example .env  # then set DEEPSEEK_API_KEY
python paper0/run_role_policy_experiment.py
# ~150 chat completions, ~38 min wall clock, ~$3 estimated spend
```

Outputs land under `outputs/role_policy/condition_{A,B,C}/<trajectory_id>/`.
The `metrics.json` file is rewritten after each (trajectory, condition)
pair so the run is resumable on crash.

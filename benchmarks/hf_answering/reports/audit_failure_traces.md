# Audit-pipeline failure traces — deepseek_only correct, audit wrong

Concrete decision-chain reconstruction (no aggregates, no guesses). The audit pipeline's FIRST verdict IS the deepseek_only decision (same call), so a failure here is the recheck/dissent losing a correct verdict. Governed pipeline: Granite extract -> DeepSeek first -> Nano audit -> DESi filter -> DeepSeek recheck. Keys in-process; core untouched.

- examples traced: 30
- deepseek_only (first) correct: 22/30; audit (final) correct: 22/30
- **deepseek-correct & audit-wrong cases: 0**
- root-cause distribution: `{}`

No such cases in this trace set: the recheck did not flip any correct first verdict to wrong (on these examples the DESi gate prevented degradation). Full per-example traces are in `reports/audit_failure_traces.jsonl`.

## Honesty / limits

- Concrete per-example chains only; classification is rule-based on the captured chain (full traces in the JSONL for verification). No aggregate interpretation, no benchmark tuning. Keys in-process; outputs secret-scanned; core unchanged.

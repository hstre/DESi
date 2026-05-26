# Audit-pipeline failure traces — deepseek_only correct, audit wrong

Concrete decision-chain reconstruction (no aggregates, no guesses). The audit pipeline's FIRST verdict IS the deepseek_only decision (same call), so a failure here is the recheck/dissent losing a correct verdict. Governed pipeline: Granite extract -> DeepSeek first -> Nano audit -> DESi filter -> DeepSeek recheck. Keys in-process; core untouched.

- examples traced: 30
- deepseek_only (first) correct: 24/30; audit (final) correct: 24/30
- **deepseek-correct & audit-wrong cases: 1**
- root-cause distribution: `{'dissent overweighting': 1}`

## vitaminc-0026 — first `REFUTES` (correct) -> final `NOT_ENOUGH_INFO` (wrong); gold `REFUTES`

**1. VitaminC sample**
- claim: As of March 16 , 2020 , there are more than 79,500 COVID-19 recoveries globally .
- evidence: As of 16 March , more than 185,000 cases of the disease have been reported in over 160 countries and territories , resulting in more than 7,300 deaths and around 79,000 recoveries .
- gold label: `REFUTES`

**2. DeepSeek-only (first solve)**
- predicted: `REFUTES` (correct)
- final line: `FINAL: REFUTES`

**3. Audit pipeline trace**
- Granite extraction: `{"claims": ["As of March 16, 2020, there are more than 79,500 COVID-19 recoveries globally."], "evidence": ["As of 16 March, more than 185,000 cases of the disease have been reported in over 160 countries and territories, resulting in more than 7,300 deaths and around 79,000 recoveries."], "polarity` (parse_ok=True)
- Nano dissent (raw): `The evidence only gives an approximate recovery count of “around 79,000” and does not specify the exact figure. Inferring that the total exceeds 79,500 therefore overreaches the available data. The claim‑evidence gap is minor. DISSENT_STRENGTH: WEAK`
- Nano parsed strength: `WEAK` (parse_ok=True)
- DESi filter: admitted=True, DESi-weight=`MEDIUM`, pruned_reason=None, authority_violation=False
- governed audit signal -> recheck: `The evidence only gives an approximate recovery count of “around 79,000” and does not specify the exact figure. Inferring that the total exceeds 79,500 therefore overreaches the available data. The claim‑evidence gap is minor. DISSENT_STRENGTH: WEAK`
- recheck verdict final line: `FINAL: NOT_ENOUGH_INFO`
- final predicted label: `NOT_ENOUGH_INFO`

**4. Delta analysis**
- what changed: verdict `REFUTES` -> `NOT_ENOUGH_INFO` at the recheck.
- info lost: the correct first verdict `REFUTES` was overturned.
- artificial uncertainty introduced: yes (final NEI, gold not NEI).
- Granite distorted evidence: no (extraction parsed).
- Nano produced dissent: yes; admitted by DESi gate: True.
- recheck degraded a correct first decision: yes.

**5. Classification: `dissent overweighting`** — the recheck accepted an admitted gap and over-abstained to NEI.

## Honesty / limits

- Concrete per-example chains only; classification is rule-based on the captured chain (full traces in the JSONL for verification). No aggregate interpretation, no benchmark tuning. Keys in-process; outputs secret-scanned; core unchanged.

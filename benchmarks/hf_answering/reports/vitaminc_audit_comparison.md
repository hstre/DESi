# Calibrated dissent-auditor comparison — vitaminc

Hypothesis: a small, sparse dissent AUDITOR (Nemotron Nano) that only marks concrete evidence gaps + a strength (NONE/WEAK/MEDIUM/STRONG) — and does NOT decide or force NEI — preserves uncertainty better than the previous auto-NEI dissent, without collapsing to blanket abstention. Pipeline: Granite extract -> DeepSeek solve -> Nano audit -> DeepSeek recheck (NEI only if the gap is concrete, claim-relevant, and unrefutable). DESi = governance alongside; DESi is not the solver.

N=10 per config (same examples). Feasibility note: Nano (free, reasoning) is ~3-10s/example and ~2/3 emit a parseable strength line; an unparseable audit degrades SAFELY to strength NONE (no dissent), so it cannot cause an all-NEI collapse. audit-parse-ok: 5/10.

Gold distribution: SUPPORTS=3, REFUTES=2, NOT_ENOUGH_INFO=5 (NEI base rate 5/10).

## Calibration comparison

| config | acc | pred NEI | NEI gap | over-abst | under-abst |
| --- | --- | --- | --- | --- | --- |
| granite_only | 0.600 | 1 | -4 | - | - |
| deepseek_only | 0.800 | 5 | +0 | - | - |
| role | 0.700 | 3 | -2 | - | - |
| audit | 0.700 | 4 | -1 | 1 | 2 |

## Auditor behavior (audit config)

- dissent strength distribution: `{'NONE': 6, 'WEAK': 4, 'MEDIUM': 0, 'STRONG': 0}`
- audit lines parsed: 5/10
- dissent accepted (recheck moved to NEI): **1**
- dissent rejected (MEDIUM/STRONG gap raised, verdict kept): **0**
- verdicts changed by recheck: 3
- branch preservation rate (strong gaps -> NEI): None
- NEI: pred 4 vs gold 5 (gap -1)

## Did calibrated dissent help (vs the all-NEI collapse of the previous layer)?

- audit NEI gap -1 vs deepseek_only +0: audit roughly calibrated. (The previous auto-NEI dissent collapsed to all-NEI, gap +5 at N=10.)
- accuracy: granite_only 0.600, deepseek_only 0.800, role 0.700, audit 0.700 -> highest **deepseek_only**.
- **audit vs deepseek_only**: acc 0.700 vs 0.800; |NEI gap| 1 vs 0 -> calibrated auditor does not beat DeepSeek-only here.

## DESi governance (alongside; core untouched)

- uncertainty improperly lost (STRONG gap, gold NEI, recheck non-NEI): 0
- challenger branches hard-pruned (substantive gap rejected): 0
- decision structure replayable: True
- DESi-core invariant across configs: True

## Honesty / limits

- Feasibility probe at small N (Nano free-tier, ~2/3 parse rate). One deterministic pass, no retries/repair/voting. Calibration read as measured. Accuracies are the model pipelines'; DESi neither solves nor scores.

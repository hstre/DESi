# SciFact / FEVER-style cross-summary — restored core

Benchmarks run on DESi. Benchmarks do not redefine DESi. DESi is not the claim reasoner.

## Evidence-style runs (DESi-core + Granite verdict behavior)

| dataset | n | acc | gold S/R/N | pred S/R/N | replay | core id | crit_pres | hard_prune | mut rej |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `pietrolesci/nli_fever` | 100 | 0.570 | 29/45/26 | 9/38/53 | 1.0 | 1.0 | 1.0 | 0 | 5/5 |
| `tals/vitaminc` | 100 | 0.540 | 31/28/41 | 63/36/1 | 1.0 | 1.0 | 1.0 | 0 | 5/5 |

## Cross questions

- **Does DESi remain invariant under evidence-style benchmarks?** YES — replay stable and core byte-identical on every evidence-style dataset; identical to the BoolQ QA run's DESi-core (replay/core/critical all 1.0 there too).
- **Does uncertainty handling (NOT_ENOUGH_INFO) create replay/core drift?** NO — the third 'abstain' class is a benchmark label, not a core state; it does not touch DESi's deterministic governance, so no replay/core drift.
- **Granite class bias on `pietrolesci/nli_fever`:** pred S/R/N = 9/38/53 vs gold 29/45/26 -> under-support, over-abstain (parse-failures 0/100).
- **Granite class bias on `tals/vitaminc`:** pred S/R/N = 63/36/1 vs gold 31/28/41 -> over-support, under-abstain (parse-failures 0/100).
- **Are branch / recoverability metrics still stable?** YES — critical_branch_preservation 1.0 and hard_pruning 0 on every dataset (no branch loss).

## Verdict

- Evidence-style (SUPPORTS/REFUTES/NOT_ENOUGH_INFO) evaluation runs cleanly on the restored core via the peripheral answering layer; DESi-core stayed invariant and identical to the QA (BoolQ) run — uncertainty/contradiction live entirely in the benchmark, not the core.

## Honesty / limits

- Canonical SciFact is unloadable (deprecated script); the real evidence source used is VitaminC (FEVER-derived) — documented, not invented. Accuracy is the MODEL's, scored exactly; DESi neither reasons nor scores.

# Conflict benchmark: P7 symbolic vs SPL projection

Same dataset, same conflict engine (predicate typing + entity normalisation). The only difference: in the SPL columns every claim is first pushed through the **vendored Alexandria SPL gate** (SemanticUnit → SemanticProjection → SPLGateway.submit → ClaimCandidate) and only **gateway-valid candidates** reach the conflict engine. No raw triple is compared directly.

- pairs: **46**
- **P7 symbolic**: raw S/P/O, no SPL gate.
- **SPL (uniform)**: SPL gate at the benchmark's uniform confidence 0.70 (every claim → E2, nothing blocked).
- **SPL (state)**: SPL gate at a *state-derived* confidence (confirmed 0.92 → E1, proposed 0.70 → E2, rejected 0.40 → E3 **block**).

| metric | P7 symbolic | SPL (uniform) | SPL (state) |
| --- | --- | --- | --- |
| exact-match | 42/46 | 42/46 | 36/46 |
| contradiction precision | 1.00 | 1.00 | 1.00 |
| contradiction recall | 1.00 | 1.00 | 0.77 |
| potential precision | 0.67 | 0.67 | 0.67 |
| alias/coref recall | 7/7 | 7/7 | 5/7 |
| multi_valued FP | 1/6 | 1/6 | 1/6 |
| homonym/merge FP | 1/2 | 1/2 | 1/2 |

## SPL gate diagnostics

| signal | SPL (uniform) | SPL (state) |
| --- | --- | --- |
| claims projected | 92 | 92 |
| gateway-invalid claims | 0 | 6 |
| pairs suppressed (a claim gated out) | 0 | 6 |
| emission rules | `{'E2': 92}` | `{'E3': 6, 'E1': 6, 'E2': 80}` |
| entropy buckets | `{'<0.25 (E1 zone)': 0, '0.25-0.65 (E2 zone)': 92, '>=0.65 (E3 block)': 0}` | `{'<0.25 (E1 zone)': 6, '0.25-0.65 (E2 zone)': 80, '>=0.65 (E3 block)': 6}` |

## What the SPL gate changed vs P7

- `neg_01` [negation] contradiction → **compatible** (state mode: a/b gated_valid=False/True, now WRONG)
- `num_01` [numeric] contradiction → **compatible** (state mode: a/b gated_valid=True/False, now WRONG)
- `tmp_01` [temporal] contradiction → **compatible** (state mode: a/b gated_valid=True/False, now WRONG)
- `attr_03` [attribute] contradiction → **compatible** (state mode: a/b gated_valid=True/False, now WRONG)
- `alias_01` [alias] contradiction → **compatible** (state mode: a/b gated_valid=False/True, now WRONG)
- `pron_01` [pronoun] contradiction → **compatible** (state mode: a/b gated_valid=True/False, now WRONG)

## Interpretation (no overclaim)

- **Does SPL improve the conflict metrics?** No. On this dataset SPL projection at uniform confidence reproduces P7 **exactly** — same precision, recall, alias/coref recall, FP counts. SPL is a projection/validation layer, not a contradiction detector: it does not rewrite subjects/objects, so it cannot by itself catch an alias or a coreference. That work still belongs to the entity-normalisation stage *inside* the conflict engine, which runs unchanged on the candidates.
- **What SPL does add (architecturally):** every claim now has to become a `SemanticUnit`, be projected to a `SemanticProjection`, and survive the gateway's emission rules (E0–E3) before it is ever comparable. The raw triple is no longer the unit of comparison — a validated `ClaimCandidate` is. Each candidate carries `h_norm`, an emission rule, and a provenance string, i.e. an auditable reason it was allowed to exist.
- **The gate is real (state mode):** when confidence carries epistemic meaning, the gate fires. Rejected claims (conf 0.40) cross τ₃ and are E3-blocked, so the pair is suppressed. This *lowers* contradiction recall on the rejected-vs-confirmed pairs — an honest, instructive negative result: the entropy gate is a **pre-filter on claim admissibility**, and coupling it naively to claim-state removes exactly the low-standing claims a contradiction check would want to see. The gate decides *what may become a claim*, not *which claims conflict*; those are different jobs.
- **Is direct raw-claim comparison now avoidable?** Yes, structurally. With `--use-spl-projection` the conflict engine only ever sees candidates emitted by `SPLGateway.submit()`; a claim that fails projection is never compared. The benchmark confirms this changes *admissibility*, not *detection quality*.

## Honesty / limits

The SPL `P_r` here is **synthesised** by the DESi adapter from the extractor's scalar confidence (peak = confidence, residual spread uniformly over a fixed synthetic relation space); it is **not** a semantic entropy measured over a real relation matrix — there is no NLP backend. So `h_norm` is a confidence-shaped quantity and the gate is, in effect, a calibrated confidence gate wearing the SPL's emission machinery. The vendored SPL code (spl.py / spl_gateway.py) is unmodified original SPL; the synthesis and the state→confidence policy are clearly-marked DESi adapter choices. SPL is not a truth solver, not NER, not an ontology.

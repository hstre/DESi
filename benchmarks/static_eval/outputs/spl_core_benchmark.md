# P9 SPL consolidation benchmark: canonical SPL-core vs vendored Alexandria

## 1. Compatibility drift (canonical core vs vendored Alexandria reference)

Same synthesised `P_r` fed to both; only the emission/admissibility logic is under test.

- projections compared: **197** (dataset claims @ uniform + state-derived confidence, plus a confidence sweep)
- emission-rule drift: **0**
- admissibility drift: **0**
- entropy drift (>1e-9): **0**

**Zero drift.** The canonical `desi.spl_core` reproduces the vendored Alexandria gateway bit-for-bit on every case. The consolidation reuses the model; it did not fork it.

## 2. Conflict metrics (SPL modes now run on canonical candidates)

| metric | P7 (raw) | SPL-uniform | SPL-state |
| --- | --- | --- | --- |
| exact-match | 42/46 | 42/46 | 36/46 |
| contradiction precision | 1.00 | 1.00 | 1.00 |
| contradiction recall | 1.00 | 1.00 | 0.77 |
| alias/coref recall | 7/7 | 7/7 | 5/7 |
| multi_valued FP | 1/6 | 1/6 | 1/6 |
| homonym/merge FP | 1/2 | 1/2 | 1/2 |
| entity_merge_uncertainty (claims) | 10 | 10 | 8 |
| projection failures (suppressed pairs) | - | 0 | 6 |
| gateway-invalid claims | - | 0 | 6 |

- SPL-uniform emission rules: `{'E2': 92}`  entropy buckets: `{'<0.25 (E1 zone)': 0, '0.25-0.65 (E2 zone)': 92, '>=0.65 (E3 block)': 0}`
- SPL-state emission rules: `{'E3': 6, 'E1': 6, 'E2': 80}`  entropy buckets: `{'<0.25 (E1 zone)': 6, '0.25-0.65 (E2 zone)': 80, '>=0.65 (E3 block)': 6}`

## 3. desi.spl_adapter (flag model) -> canonical candidate

The third layer has no triple and no entropy; it maps onto the same `CanonicalClaimCandidate` via the flag path (entropy stays `None`):

```
content='water boils at 100C'              conf=0.9 amb=False rels=0 -> admissible=True reason='' entropy=None origin=desi_spl_adapter
content='unclear proposition'              conf=0.4 amb=True rels=0 -> admissible=False reason='ambiguous_claim' entropy=None origin=desi_spl_adapter
content='x supports y'                     conf=0.9 amb=False rels=1 -> admissible=False reason='hallucinated_relation' entropy=None origin=desi_spl_adapter
content=''                                 conf=0.9 amb=False rels=0 -> admissible=False reason='empty_content' entropy=None origin=desi_spl_adapter
```

## Interpretation (no overclaim)

- **Architectural gain, not benchmark gain.** P9 reproduces P7/P8 conflict metrics exactly and drifts from the vendored Alexandria by zero. The value is one entropy model, one gateway, one ClaimCandidate, and a clean `src`-owned home — not better contradiction detection.
- **SPL stays an admissibility / projection layer.** As P8 showed and P9 preserves: the gate decides *what may become a comparable claim*; the conflict engine decides *which claims conflict*. Consolidation did not (and should not) collapse those two jobs.
- **Two uncertainty models still exist**, honestly. The entropy model (Alexandria / synth `P_r`) and the flag model (`desi.spl_adapter`: boolean ambiguous + confidence floor) both live behind the one gateway via `admit_projection` / `admit_flag`. Unifying them needs a real `P_r` for the flag model (an NLP backend) — deferred, not faked.
- **`P_r` is synthesised from confidence**, so `h_norm` is confidence-shaped, not a measured semantic entropy. Not a truth solver, not NER, not ontology.

# Reproduce v3.1 — Documentation Claim-Anchor Discipline

v3.1 inserted inline `[claim-anchor: ...]` markers next to every
quantitative claim in v2.x docs and tagged pre-v2.0 documents with
explicit `[legacy-unanchored]` markers. This reduced the
v3.0-measured `self_deception_rate` from 0.314 to 0.05144 — a
6.11× improvement.

## The minimal reproduction

```bash
PYTHONPATH=src pytest tests/doc_anchors/ -q
```

Expected output:

```
41 passed
```

Expected runtime: ~2s.

## What the 41 tests prove

The 41 doc-anchor tests are partitioned into six groups:

| Group | Count | What it verifies |
| --- | ---: | --- |
| `test_schema.py` | 7 | Anchor parser is single-line, whitespace-tolerant, case-sensitive on keys |
| `test_validator.py` | 9 | Validator produces correct verdict for every `AnchorVerdict` case |
| `test_corpus_anchors.py` | 8 | Every anchor in the real docs verifies; no duplicates; every v0.x/v1.x doc carries `[legacy-unanchored]`; no v2.x doc does |
| `test_negative_control.py` | 4 | Fake anchor with missing artefact, wrong value, and unknown field all rejected |
| `test_improvement.py` | 5 | `self_deception_rate < 0.20`, `verified_claims > 321`, `drift_findings == 0`, improvement_factor ≥ 1.5× |
| `test_regression.py` | 8 | v1.5 / v1.9 / v2.3 metrics unchanged; v2.8 replay hashes pinned; no production package imports `doc_anchors` |

## What the anchor schema looks like

```
precision: 1.000  [claim-anchor: artifact=artifacts/v2_8/reconstruction.json, field=benchmark_hash_before, expected=aa01151d6e165bf0]
```

Three required keys: `artifact`, `field`, `expected`. Single-line.
Whitespace-tolerant between commas. Case-sensitive on keys.

Legacy marker for pre-v2.0 docs:

```
<!-- [legacy-unanchored] — pre-v2.0 prose report; no JSON artefact exists for this version. -->
```

## What the audit measured

`artifacts/v3_1/audit.json`:

```
total_documents     : 35
total_claims        : 486
verified_claims     : 461
unverifiable_claims : 25
hash_mismatch_claims: 0
value_mismatch_claims: 0
ambiguous_claims    : 23
drift_findings_count: 0
self_deception_rate : 0.05144
replay_hash         : 3dbdf57f882a981a
```

`artifacts/v3_1/anchors.json`:

```
total_anchors    : 36
verified_anchors : 36   (100 %)
invalid_anchors  :  0
legacy_exemptions: 19
replay_hash      : 15ba5f929b38bde8
```

## Anchored claims

| Claim | Statement | Artefact | Field | Expected |
| --- | --- | --- | --- | --- |
| RB-055 | v3.1 audit drift findings = 0 | `artifacts/v3_1/audit.json` | `drift_findings_count` | `0` |
| RB-056 | v3.1 audit hash mismatches = 0 | `artifacts/v3_1/audit.json` | `hash_mismatch_claims` | `0` |
| RB-057 | 36 total anchors | `artifacts/v3_1/anchors.json` | `total_anchors` | `36` |
| RB-058 | 36 verified anchors | `artifacts/v3_1/anchors.json` | `verified_anchors` | `36` |
| RB-059 | 0 invalid anchors | `artifacts/v3_1/anchors.json` | `invalid_anchors` | `0` |
| RB-060 | 19 legacy exemptions | `artifacts/v3_1/anchors.json` | `legacy_exemptions` | `19` |

Verified by `tests/reviewer_bundle/test_claim_index.py::
test_each_claim_value_matches_artifact[RB-055..060]`.

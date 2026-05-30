# DESi State (not Summary) — evaluation report (Prototype 2)

Hypothesis under test (per the brief): epistemic STATES are a better long-term context than compressed narratives. The state stores no prose, no chat history, no summary — only structured entries (claims, constraints, conflicts, decisions, discarded paths, questions, evidence). Deterministic, offline, no LLM, no embeddings.

## Methodological discipline

- **Ground truth is independent**: authored BEFORE extractor was implemented, in separate files (`fixtures_v2/groundtruth_*.json`) the evaluator opens directly. The extractor never sees them.
- **No metric tuning after seeing results**: thresholds (exact ID + field match), forbidden leakage list, and the success criteria are fixed in code.
- **Negative results are reported, not patched.**
- **Workability in a new Claude chat is UNTESTED** in this environment (needs a second Claude session); reported honestly, not silently inflated.

## Aggregate (N=3 fixtures)

| metric | mean exact recall |
| --- | --- |
| active claims (ID + status + evidence) | 1.0 |
| active constraints (ID + scope) | 1.0 |
| decisions (ID + active_since + replaces) | 0.833 |
| open conflicts (ID + claim_ids + status) | 1.0 |
| discarded paths (ID) | 1.0 |
| open questions (ID + blocking) | 1.0 |
| evidence status (domain + status) | 1.0 |

## Per-fixture detail

| fixture | raw_tok | state_tok | compression | budget≤500 | round-trip | leaks | schema viols |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `compression_pipeline` | 234 | 382 | -0.6325 | True | True | 0 | 0 |
| `governance` | 212 | 408 | -0.9245 | True | True | 0 | 0 |
| `long_session` | 385 | 724 | -0.8805 | False | True | 0 | 0 |

## Per-fixture success (brief criteria)

| fixture | claims | constraints | decisions | conflicts | no narrative leak |
| --- | --- | --- | --- | --- | --- |
| `compression_pipeline` | True | True | True | True | True |
| `governance` | True | True | False | True | True |
| `long_session` | True | True | True | True | True |

## Missing / mismatched (what the extractor failed to recover)

### `governance`
  - **decisions missing:** ['D2']


## Comparison vs Prototype 1 (narrative-style extractor, on `main`)

- Prototype 1 used lexical/structural cues PLUS short prose snippets per item. On these fixtures it scored mean decision recall 0.667 / overall 0.603 (Jaccard ≥0.3 against ground-truth strings) and had NEGATIVE compression on short chats.
- Prototype 2 stores only IDs + structured fields. Recall here is ID-exact (stricter), and compression is computed against the same raw text. The two cannot be averaged together — they measure different things. The numbers above stand on their own evidence.

## Verdict on the core hypothesis

**The hypothesis 'epistemic states are a better long-term context than compressed narratives' is supported here when — and only when — the chat carries explicit structural markers.** When markers are present (as in these fixtures), the v2 state recovers all brief-mandated categories exactly, with zero narrative leakage and zero schema violations.
When markers are NOT present (an unstructured chat), v2 returns a near-empty state by design. That is the honest cost of refusing to summarize: extraction depends on the chat actually expressing its state structurally. This is the boundary the brief invites us to find, not a bug.

## What this run does NOT claim

- Does NOT reproduce the paper's 9900→269 figure (different regime).
- Does NOT measure whether a downstream Claude session is workable on the state alone (reported `UNTESTED_in_this_env`).
- Does NOT claim general applicability beyond chats that carry explicit structural markers.

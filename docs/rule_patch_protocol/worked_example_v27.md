# Worked Example — v2.7 `CAUSAL_CHAIN`

The v2.7 CAUSAL_CHAIN patch is the first DESi rule change that
implicitly satisfied the v2.8 protocol. v2.8 replays it
deterministically; the artefact lives at
`artifacts/v2_8/reconstruction.json` and resolves to
`replay_hash = 1f4d9dfe44cb16e1`.

This document is the trace, phase by phase. No simplification —
every number below comes from a real artefact under `artifacts/`.

---

## Discovery evidence

DISCOVERY required three predecessor artefacts:

| Artefact | What it provided |
| --- | --- |
| `artifacts/v2_4/report.json` | Bridge-entry funnel: 77% of multistep cases die at `PARSER_UNSUPPORTED_FORM` despite `premise_count > 0`. |
| `artifacts/v2_5/report.json` | Rule-coverage probe: `rule_hit_rate = 0.000`. Dominant missing class = `causal_chain` (20/30). |
| `artifacts/v2_6/report.json` | Causal-chain coverage probe: `multistep_trigger_rate = 0.733`; `main_trigger_rate = 0.020`; **`known_false_positive_reopen_rate = 0.000`**. |

The v2.7 candidate's `required_artifacts` field declares exactly
these three. The protocol's DISCOVERY phase hashes each file to
record an exact snapshot of the evidence base at decision time:

```
v2_4/report.json  → sha256[:16]
v2_5/report.json  → sha256[:16]
v2_6/report.json  → sha256[:16]
```

---

## Risk metrics (read from v2.6)

| Metric | Value | Gate |
| --- | ---: | :-: |
| `multistep_trigger_rate` | 0.733 | informational |
| `main_trigger_rate` | 0.020 | informational |
| `known_false_positive_reopen_rate` | **0.000** | ✅ must be 0.0 |
| `authority_touch_rate` | **0.000** | ✅ must be 0.0 |
| `philosophy_touch_rate` | **0.000** | ✅ must be 0.0 |
| `metaphor_touch_rate` | 0.000 | informational |
| `safe_to_implement` | **true** | ✅ must be true |

All four hard gate conditions met. RISK_PROBE phase returns
`passed = True` with `reason = "probe clean"`.

---

## Derived guards (synthesised from v2.6 + v2.7)

The seven guards declared by the v2.7 candidate. Each carries an
`observable` from the closed allowlist; none uses `case_id` or
`allowlist`.

| # | Guard name | Observable | Forbidden shape |
| -: | --- | --- | --- |
| 1 | `contradiction_first_by_iteration_order` | `rule_iteration_order` | premise set already matched by `CONTRADICTION` |
| 2 | `premise_kind_atomic_or_particular` | `premise_kind` | `universal` / `conditional` / `implication` / `authority` |
| 3 | `negation_marker_guard` | `premise_text_substring` | contains ` not `, `n't `, ` never `, ` none `, ` no ` |
| 4 | `quantifier_marker_guard` | `premise_text_substring` | contains ` all `, ` every `, ` some `, ` any `, ` each ` |
| 5 | `cycle_connective_guard` | `premise_text_substring` | contains ` because `, ` depends on `, ` requires `, ` relies on `, ` uses ` |
| 6 | `token_in_three_premises_cycle_guard` | `premise_token_graph` | content token appears in 3+ distinct premises |
| 7 | `recycled_conclusion_token_guard` | `conclusion_token_overlap` | conclusion content token appears in 2+ distinct premises |

GUARD_SYNTHESIS phase returns `passed = True` with `reason = "7
guards approved"`.

---

## Implementation diff

`PatchCandidate.touched_files` declares 8 files:

```
src/desi/logic/inference.py
src/desi/rule_audit/categories.py
tests/logic/test_inference.py
tests/logic/test_causal_chain.py
tests/logic/test_causal_chain_regression.py
tests/rule_audit/test_categories.py
docs/memory/v2_7.md
artifacts/v2_7/report.json
```

Of the production-code files, **only one** (`src/desi/logic/inference.py`)
contains rule logic. The second
(`src/desi/rule_audit/categories.py`) is a one-line update to a
mirror enum required by the v2.5 audit invariant. The remaining
six are tests, docs, and the artefact. IMPLEMENTATION phase
verifies every file exists on disk and lives under an allowed
root.

---

## Regression hashes

The protocol computed `compute_benchmark_hashes()` twice during the
v2.7 reconstruction; both calls returned identical six-tuples:

```
v1_5_main         : <same before/after>
v1_9_tool         : <same before/after>
v2_3_multistep    : <same before/after>
v2_4_bridge_audit : <same before/after>
v2_5_rule_audit   : <same before/after>
v2_6_causal_probe : <same before/after>
```

Aggregate signature: `benchmark_hash_before == benchmark_hash_after
== aa01151d6e165bf0`. REGRESSION phase returns `passed = True`
with `reason = "all six benchmark hashes identical to baseline"`.

---

## Replay proof

REPLAY_VERIFICATION runs `compute_benchmark_hashes()` a third and
fourth time and compares both to the previous pair. Result:
identical. The phase returns
`reason = "two consecutive runs match bit-for-bit"`.

Outside the protocol, an independent replay confirms the record's
own `replay_hash`:

```
First run  : replay_hash = 1f4d9dfe44cb16e1
Second run : replay_hash = 1f4d9dfe44cb16e1
```

Verified by `tests/rule_patch_protocol/test_protocol.py::
test_two_runs_of_v27_reconstruction_match`.

---

## Final record

```
patch_id              : pp_<sha256[:16] over candidate>
target_rule           : causal_chain
source_branch         : feature/causal-chain-rule-guarded
phase                 : complete
passed                : true
created_guards        : [7 names listed above]
touched_files         : [8 paths listed above]
benchmark_hash_before : aa01151d6e165bf0
benchmark_hash_after  : aa01151d6e165bf0
replay_hash           : 1f4d9dfe44cb16e1
phase_outcomes        : 6 outcomes, all passed
fail_reason           : (empty)
```

Full JSON at `artifacts/v2_8/reconstruction.json`.

Every quantitative claim in this document is checked by
`tests/protocol_docs/test_doc_consistency.py`.

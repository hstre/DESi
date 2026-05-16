# DESi Cross-LLM Blind Review — Reviewer Prompt

You are reviewing a research repository called **DESi** with **no
prior knowledge** of the project. You may not look at any author
commentary, no chat history, no Slack threads. Your inputs are
the files on disk under `docs/`, `artifacts/`, and `tests/`.

---

## What DESi claims

1. A new inference rule `CAUSAL_CHAIN` was added in v2.7 to
   `src/desi/logic/inference.py`. It accepts linear cause-effect
   chains (≥ 2 atomic premises + 1 atomic conclusion, no
   negation, no quantifier, no cyclic connectives).
2. The v1.5 main benchmark (precision/recall/false_positives =
   1.0/1.0/0) was preserved bit-for-bit after v2.7.
3. The v2.8 patch protocol can reconstruct the v2.7 patch and
   produces `replay_hash = 1f4d9dfe44cb16e1`.
4. The v2.8 patch protocol rejects a fake patch with empty
   guards and produces `replay_hash = d83d81ab8417c022`.
5. The v3.1 doc-anchor pass reduced the v3.0 measured
   `self_deception_rate` from `0.314` to `0.05144`.

## What DESi does NOT claim

1. DESi is not a general-purpose reasoning agent.
2. DESi does not use an LLM at runtime.
3. DESi does not claim its parser handles arbitrary English.
   v2.3 measured 18/30 multi-step cases blocked at parser stage.
4. DESi does not claim to solve `R5` cycle detection
   structurally. v2.4 measured 0/6 R5 cases as
   `RESOLUTION_CYCLE_DETECTED`.
5. DESi does not claim that depth-knob mutation produces
   measurable improvement on v1.9 texts (v2.2 measured flat
   fitness across `max_depth ∈ {1..6}`).

## What artifacts exist

```
artifacts/v2_0/report.json          # sandbox 30-step run
artifacts/v2_1/report.json          # self-diagnostic
artifacts/v2_2/report.json          # depth-sandbox 30-step run
artifacts/v2_3/report.json          # multi-step benchmark
artifacts/v2_4/report.json          # bridge-entry audit
artifacts/v2_5/report.json          # rule-coverage audit
artifacts/v2_6/report.json          # causal-chain probe
artifacts/v2_7/report.json          # post-patch metrics
artifacts/v2_8/reconstruction.json  # protocol reconstruction
artifacts/v2_8/fail_case.json       # protocol fake-patch rejection
artifacts/v3_0/report.json          # first self-audit of docs
artifacts/v3_1/audit.json           # post-anchor self-audit
artifacts/v3_1/anchors.json         # anchor coverage report
artifacts/v3_2/reviewer_metrics.json
```

## What hashes matter

| Name | Expected | Source |
| --- | --- | --- |
| v2.8 reconstruction `replay_hash` | `1f4d9dfe44cb16e1` | `artifacts/v2_8/reconstruction.json#replay_hash` |
| v2.8 fail-case `replay_hash` | `d83d81ab8417c022` | `artifacts/v2_8/fail_case.json#replay_hash` |
| v2.0 sandbox `replay_hash` | `21a692fb35c8f368` | `artifacts/v2_0/report.json#replay_hash` |
| v3.1 audit `replay_hash` | `3dbdf57f882a981a` | `artifacts/v3_1/audit.json#replay_hash` |
| v3.1 anchors `replay_hash` | `15ba5f929b38bde8` | `artifacts/v3_1/anchors.json#replay_hash` |

## What you may assume

- Every file under `artifacts/` is the exact byte content the
  authors committed.
- Every test in `tests/` runs without network access and
  without API keys.
- The 50 v1.5 main benchmark cases and 30 v2.3 multi-step cases
  are immutable across v2.x.

## What you may NOT assume

- That any unstated number is correct.
- That an absent test is implicit.
- That a claim without an `artifacts/` reference is verified.
- That what the docs say *about* the runtime is what the
  runtime *does*. Re-run benchmarks via
  `python -m pytest tests/` to confirm.

## Your job

Answer exactly 5 questions (see `questions.md`). Each answer
must be falsifiable: cite a file path, a field path, or a test
name. No prose-only opinions.

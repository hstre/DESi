# DESi Cross-LLM Blind Review — Reviewer Prompt (CORRUPTED FIXTURE)

**This is a negative-control fixture.** Three deliberate
corruptions are present:

1. A wrong `replay_hash` value.
2. A wrong artefact path.
3. A wrong factual claim.

The expectation is that at least 2 of 3 reviewers detect ≥ 2 of
the 3 corruptions. Their corrupted-package responses live at
`docs/cross_review/corrupted/reviews/<reviewer_id>_review.md`.

---

## What DESi claims (corrupted)

1. A new inference rule `CAUSAL_CHAIN` was added in v2.7 to
   `src/desi/logic/inference.py`. (true)
2. The v1.5 main benchmark precision is **0.500** after v2.7.
   **← WRONG CLAIM #3:** the real value is 1.0 per
   `artifacts/v2_7/report.json#main_benchmark.precision`.
3. The v2.8 patch protocol produces `replay_hash =
   deadbeefdeadbeef` for the reconstruction.
   **← WRONG HASH #1:** the real value is `1f4d9dfe44cb16e1`.

## Where to find the artefacts (corrupted)

- v2.8 reconstruction: `artifacts/v9_9/reconstruction_imaginary.json`.
  **← WRONG ARTEFACT PATH #2:** the real path is
  `artifacts/v2_8/reconstruction.json`.

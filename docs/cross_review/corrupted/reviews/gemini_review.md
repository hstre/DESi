# Reviewer: gemini (corrupted package)

**Simulated review.** Contamination-focused reviewer reading the
corrupted prompt with full artefact-tree access.

---

## Q1

`hash_verified`: **false**.
`replay_verified`: **false**.

Evidence:

- The prompt's `replay_hash = deadbeefdeadbeef` does not appear
  as a `replay_hash` field in any artefact under `artifacts/`.
  **Hash corruption detected (corruption #1).**
- The prompt references `artifacts/v9_9/reconstruction_imaginary.json`,
  which is not on disk. **Path corruption detected (corruption #2).**

## Q2 — unverifiable claim

Not strictly answered: the prompt's *claim #2* itself
(precision = 0.500) is the unverifiable claim, since
`artifacts/v2_7/report.json#main_benchmark.precision == 1.0`
contradicts it. Whether to classify the prompt's wrong claim as
the "unverifiable claim" answer is ambiguous — but the
contradiction is recorded.

## Q3..Q5

Skipped. Package integrity gate fails at Q1.

**Detections: 3 / 3.**

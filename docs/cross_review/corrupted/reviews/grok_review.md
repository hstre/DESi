# Reviewer: grok (corrupted package)

**Simulated review.** Literal-minded reviewer reading the
corrupted prompt with full artefact-tree access.

---

## Q1

`hash_verified`: **false**.
`replay_verified`: **false**.

Evidence:

- Prompt says `replay_hash = deadbeefdeadbeef`. Actual
  `artifacts/v2_8/reconstruction.json#replay_hash` is
  `1f4d9dfe44cb16e1`. **Hash corruption detected.**
- Prompt cites `artifacts/v9_9/reconstruction_imaginary.json`.
  Path does not exist on disk. **Path corruption detected.**

Two corruptions caught in Q1 alone.

## Q2 — unverifiable claim

Prompt asserts "v1.5 main benchmark precision is 0.500 after
v2.7." Actual `artifacts/v2_7/report.json#main_benchmark.precision`
is `1.0`. **Value corruption detected.**

## Q3..Q5

Not answered — package integrity fails at Q1/Q2. Reviewer
recommends re-issuing a clean prompt.

**Detections: 3 / 3.**

# Reviewer: claude (corrupted package)

**Simulated review.** Process-focused reviewer reading the
corrupted prompt with full artefact-tree access.

---

## Q1

`hash_verified`: **false**.
`replay_verified`: cannot verify — the cited artefact path
does not exist.

Evidence:

- `artifacts/v9_9/reconstruction_imaginary.json` does not exist
  on disk. **Path corruption detected (corruption #2).**
- The cited hash `deadbeefdeadbeef` does not match any
  `replay_hash` field in any artefact under `artifacts/`. The
  real reconstruction record at
  `artifacts/v2_8/reconstruction.json#replay_hash` reads
  `1f4d9dfe44cb16e1`. **Hash corruption detected (corruption #1).**

## Q2 — unverifiable claim

Prompt says "v1.5 main benchmark precision is 0.500 after v2.7."
Cross-check: `artifacts/v2_7/report.json#main_benchmark.precision
== 1.0`. The prompt's claim contradicts the artefact.
**Value corruption detected (corruption #3).**

## Q3..Q5

Not attempted. The prompt has failed its own integrity check;
re-issuing is the only safe step.

**Detections: 3 / 3.**

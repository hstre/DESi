# Claim memory: P0 (direct recorder) vs P1 (run_desi memory_hook)

- Records: **50** (P0) / **50** (P1)

| metric | P0 direct | P1 via memory_hook |
| --- | --- | --- |
| total claims in store | 93 | 200 |
| answer-claim states | `{'confirmed': 17, 'rejected': 8, 'proposed': 25}` | `{'confirmed': 17, 'rejected': 8, 'proposed': 25}` |
| relations in store | `{'SUPPORTS': 18, 'CONTRADICTS': 8}` | `{'DERIVES_FROM': 50, 'SUPPORTS': 18, 'CONTRADICTS': 8}` |
| MemoryHook used | n/a (direct recorder) | 50/50 tasks |
| claims written by run_desi hook | 0 (run_desi not used for claims) | 100 (trajectory focus claims) |
| run_desi steps governed | 0 | 100 |

## How claims were written

- **P0:** answer + gold claims written **directly** via `MemoryRecorder` in one run; `run_desi` not involved.
- **P1:** `run_desi(trajectory, memory_hook=MemoryHook(...))` is genuinely called per task. The hook writes the **trajectory's focus claims** (state PROPOSED, content = focus id) + a `DERIVES_FROM` edge, and `run_desi` returns DeterministicMetrics. The **answer/gold semantics** (CONFIRMED/REJECTED + SUPPORTS/CONTRADICTS) are then recorded by the adapter through the same recorder — because the stock MemoryHook does not map a benchmark decision to a ClaimState (it only mirrors trajectory focus). This is stated explicitly, not hidden.

## Equivalence of the semantic layer

- Answer-claim states identical P0 vs P1: **True** (the semantic recording is the same code path; P1 only adds the run_desi/hook trajectory layer on top).

> P1 is closer to the DESi core: claims now enter through the `run_desi` governance lifecycle (Run + OperatorEvents + replay-safe hook), not only a side-channel recorder call. The remaining gap is that the hook does not yet carry benchmark answer→ClaimState semantics; bridging that inside a custom hook is the next step.

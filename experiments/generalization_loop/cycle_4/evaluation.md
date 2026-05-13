# Cycle 4 evaluation — strict-> on attractor dup threshold

pytest **33 passed** (unchanged — no new test for a 1-char operator swap).

## Metrics

| Metric | Cycle 3 | Cycle 4 | Δ |
|---|---:|---:|---:|
| n=20 attractor_lock fires | 5 | **4** | -1 (gen04 released) |
| n=10 attractor_lock fires | 5 | 5 | 0 |
| n=20 spurious-hit total | 15 | 14 | -1 |
| pytest | 33 | 33 | 0 |

## Verdict

**ACCEPTED.** Targeted false-positive release without regression.

## Next-cycle hint

gen12 has 5 ENs total with two confirmed genuines at loops 1 and 5;
penultimate detector only inspects loops 7,9 — misses intermediate
confirmed genuines. Cycle 5 candidate: scan all-vs-last not just
penultimate-vs-last.

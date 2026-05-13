# Cycle 3 evaluation — tail-windowed branch_explosion averaging

pytest **33 passed** (32 prior + 1 new for the recovery-suppression case).

## Metrics

| Metric | Cycle 2 | Cycle 3 | Δ |
|---|---:|---:|---:|
| n=20 branch_explosion fires | 2 | 2 | 0 (composition shifted) |
| n=10 branch_explosion fires | 1 | 1 | 0 |
| pytest | 32 | **33** | +1 |

## Composition delta (n=20 branch_explosion)

| Fixture | Cycle 2 | Cycle 3 | _meta says |
|---|:---:|:---:|---|
| gen04 | True | **False** | should be False (recovery) |
| gen06 | False | **True** | should be True |
| gen17 | True | **False** | should be False (recovery) |
| gen18 | False | **True** | should be True |

Two false positives suppressed; two true positives surfaced.

## Verdict

**ACCEPTED.** Same headline count, materially better classification.

## Next-cycle hint

`attractor_lock` still fires on gen04 with tail mean_novel=3.0, mean_dup=0.30 —
exactly at the cycle-1 boundary. The trajectory just recovered via synthesis.
The cycle-1 thresholds need a stricter boundary on the dup side (mean_dup > 0.30
instead of >=) to release gen04 from the attractor classification too.

Cycle 4 candidate: tighten ATTRACTOR_TAIL_MIN_MEAN_DUP from 0.30 to >0.30.

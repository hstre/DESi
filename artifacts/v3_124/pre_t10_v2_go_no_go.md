# DESi v3.124 — Pre-T10 v2 Go / No-Go

**Killerfrage:** Welche Pre-T10 Variante geht in Produktion — oder gar keine?

**Verdict:** `DEPLOY_MULTI_SIGNAL`

## Strategy comparison

Each strategy is evaluated against the v3.119 ground-truth recoverability labels (52 cross-family blindness pools, 16 rescuable / 36 non-rescuable).

| Strategy | Rule | FAR | TPR | Complexity | Allowed | Blocked | FAR ≤ 0.10 | TPR ≥ 1.0 | architecture_roi | Qualifies |
|---|---|---:|---:|---:|---:|---:|:---:|:---:|---:|:---:|
| `no_precheck` | allow every pool through to T10 | 0.692308 | 1.0 | 0 | 52 | 0 | ✗ | ✓ | 0.000000 | ✗ |
| `single_threshold` (v3.120) | `text_variance ≥ 0.541667` | 0.111111 | 1.0 | 1 | 18 | 34 | ✗ | ✓ | 0.581197 | ✗ |
| `multi_signal` (v3.123) | `text_variance ≥ 0.541667 AND members_per_family ≥ 1.5` | 0.000000 | 1.0 | 2 | 16 | 36 | ✓ | ✓ | 0.346154 | ✓ |

`architecture_roi` = (baseline_far − strategy_far) / max(complexity, 1), measuring per-complexity reduction in false-activation relative to the no-precheck baseline.

## Pflichtmetriken

| Metric | Value |
|---|---|
| `best_strategy` | `multi_signal` |
| `false_activation_rate` | 0.000000 |
| `true_case_recall` | 1.000000 |
| `architecture_roi` | 0.346154 |
| `replay_stability` | 1.000000 |

## Why the highest-ROI strategy did not win

`single_threshold` has a higher per-complexity ROI (0.581 vs 0.346) because it cuts more of the baseline FAR with a single threshold. It is nevertheless disqualified: its FAR (0.111) exceeds the deployment ceiling (0.10), so it would still leak 2 unrescuable pools per ~18 activations into T10.

The decision rule is therefore: **first** require both gates (`FAR ≤ 0.10`, `TPR ≥ 1.0`) to pass; **then** pick the lowest-complexity qualifying strategy, with `architecture_roi` as the tiebreaker. Only `multi_signal` qualifies, so it wins outright.

## Disqualified strategies

* `no_precheck`: FAR = 0.692 — far above the ceiling. Baseline reference only.
* `single_threshold`: FAR = 0.111 — fails by 0.011. Structurally infeasible without a second axis: the 2 false-positive pools (pid 16, 17) sit between rescuable pools' text_variance values.

## Replay stability

`replay_stability` = 1.0. The strategy ranking, metric values, and best-strategy verdict are deterministic across repeated builds. No bootstrap noise, no subprocess hash drift, no PYTHONHASHSEED dependency.

## Decision

**Deploy `multi_signal` as the pre-T10 gate.** The rule is:

```
allow_t10(pool)  ⇔  text_variance(pool) ≥ 0.541667
                    AND members_per_family(pool) ≥ 1.5
```

* zero false activations on the v3.119 ground truth,
* every rescuable pool let through,
* two thresholds, both interpretable (text_variance from v3.117/v3.119; members_per_family from the closed pool structure),
* deterministic and replay-stable.

`single_threshold` remains as the v3.120 experimental baseline; do not deploy. `no_precheck` is rejected — the cost of T10 misapplication on 69% of pools is unacceptable.

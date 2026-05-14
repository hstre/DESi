# Cycle 3 — native-DES operation taxonomy report

**Source**: `experiments/external_reality_challenge/source/des_state.json`
**Total operations**: 35

## Per-category counts

| Category | Count | % |
|---|---:|---:|
| `reconstructed_EN_candidate` | 3 | 8.6% |
| `reconstructed_critique_navigation_candidate` | 3 | 8.6% |
| `plain_operator_transition` | 29 | 82.9% |
| `unsupported_extension` | 0 | 0.0% |
| `unparsed_operation` | 0 | 0.0% |
| **TOTAL** | **35** | **100.0%** |

## Coverage measurements

- **coverage (reconstructed / total)**: 6 / 35 = 17.1%
- **unparsed rate**: 0 / 35 = 0.0%
- **unsupported rate** (parsed but no reconstruction rule): 0 / 35 = 0.0%
- **target-creating completeness**: 6 / 6 target-creating ops landed in a reconstruction category = 100.0%

## Per-operation classification (n=35)

| Loop | Category | Operator | Sub-role | Source | Target | Raw |
|---:|---|---|---|---|---|---|
| 0 | `plain_operator_transition` | `T3` | `-` | `C001` | `-` | `T3 on C001` |
| 1 | `plain_operator_transition` | `T4` | `-` | `C001` | `-` | `T4 on C001` |
| 2 | `plain_operator_transition` | `T3` | `-` | `C002` | `-` | `T3 on C002` |
| 3 | `reconstructed_EN_candidate` | `T6` | `hypothesis_builder` | `C002` | `C004` | `T6[hypothesis_builder] on C002 -> C004` |
| 4 | `reconstructed_critique_navigation_candidate` | `T6` | `falsifier` | `C002` | `C005` | `T6[falsifier] on C002 -> C005` |
| 5 | `plain_operator_transition` | `T8` | `-` | `C002` | `-` | `T8 on C002` |
| 6 | `plain_operator_transition` | `T3` | `-` | `C003` | `-` | `T3 on C003` |
| 7 | `reconstructed_EN_candidate` | `T5` | `hypothesis_builder` | `C003` | `C006` | `T5[hypothesis_builder] on C003 -> C006` |
| 8 | `reconstructed_critique_navigation_candidate` | `T5` | `falsifier` | `C003` | `C007` | `T5[falsifier] on C003 -> C007` |
| 9 | `plain_operator_transition` | `T2` | `-` | `C003` | `-` | `T2 on C003` |
| 10 | `reconstructed_EN_candidate` | `T6` | `hypothesis_builder` | `C003` | `C008` | `T6[hypothesis_builder] on C003 -> C008` |
| 11 | `reconstructed_critique_navigation_candidate` | `T6` | `falsifier` | `C003` | `C009` | `T6[falsifier] on C003 -> C009` |
| 12 | `plain_operator_transition` | `T8` | `-` | `C003` | `-` | `T8 on C003` |
| 13 | `plain_operator_transition` | `T3` | `-` | `C004` | `-` | `T3 on C004` |
| 14 | `plain_operator_transition` | `T7` | `-` | `C004` | `-` | `T7 on C004` |
| 15 | `plain_operator_transition` | `T6` | `-` | `C004` | `-` | `T6 on C004` |
| 16 | `plain_operator_transition` | `T8` | `-` | `C004` | `-` | `T8 on C004` |
| 17 | `plain_operator_transition` | `T3` | `-` | `C005` | `-` | `T3 on C005` |
| 18 | `plain_operator_transition` | `T7` | `-` | `C005` | `-` | `T7 on C005` |
| 19 | `plain_operator_transition` | `T6` | `-` | `C005` | `-` | `T6 on C005` |
| 20 | `plain_operator_transition` | `T8` | `-` | `C005` | `-` | `T8 on C005` |
| 21 | `plain_operator_transition` | `T3` | `-` | `C006` | `-` | `T3 on C006` |
| 22 | `plain_operator_transition` | `T6` | `-` | `C006` | `-` | `T6 on C006` |
| 23 | `plain_operator_transition` | `T8` | `-` | `C006` | `-` | `T8 on C006` |
| 24 | `plain_operator_transition` | `T3` | `-` | `C007` | `-` | `T3 on C007` |
| 25 | `plain_operator_transition` | `T7` | `-` | `C007` | `-` | `T7 on C007` |
| 26 | `plain_operator_transition` | `T6` | `-` | `C007` | `-` | `T6 on C007` |
| 27 | `plain_operator_transition` | `T8` | `-` | `C007` | `-` | `T8 on C007` |
| 28 | `plain_operator_transition` | `T3` | `-` | `C008` | `-` | `T3 on C008` |
| 29 | `plain_operator_transition` | `T6` | `-` | `C008` | `-` | `T6 on C008` |
| 30 | `plain_operator_transition` | `T8` | `-` | `C008` | `-` | `T8 on C008` |
| 31 | `plain_operator_transition` | `T3` | `-` | `C009` | `-` | `T3 on C009` |
| 32 | `plain_operator_transition` | `T7` | `-` | `C009` | `-` | `T7 on C009` |
| 33 | `plain_operator_transition` | `T6` | `-` | `C009` | `-` | `T6 on C009` |
| 34 | `plain_operator_transition` | `T8` | `-` | `C009` | `-` | `T8 on C009` |


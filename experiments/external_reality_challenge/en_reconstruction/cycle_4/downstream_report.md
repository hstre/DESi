# Cycle 4 — downstream-effect validation report

**Source**: `experiments/external_reality_challenge/source/des_state.json`
**Candidates analysed**: 6
**Threshold** (PRODUCTIVE_MIN_TOUCHES): 3

## Classification summary

| Class | Count |
|---|---:|
| `productive` | 5 |
| `dormant` | 0 |
| `terminal_anchor` | 1 |
| **TOTAL** | **6** |

## Per-candidate downstream effect

| Claim | Created @ loop | Via | First focus after | Touches | Survives | Terminal focus | Classification |
|---|---:|---|---:|---:|:---:|:---:|---|
| `C004` | 3 | `T6[hypothesis_builder]` | 13 | 4 | ✓ | ✗ | `productive` |
| `C005` | 4 | `T6[falsifier]` | 17 | 4 | ✓ | ✗ | `productive` |
| `C006` | 7 | `T5[hypothesis_builder]` | 21 | 3 | ✓ | ✗ | `productive` |
| `C007` | 8 | `T5[falsifier]` | 24 | 4 | ✓ | ✗ | `productive` |
| `C008` | 10 | `T6[hypothesis_builder]` | 28 | 3 | ✓ | ✗ | `productive` |
| `C009` | 11 | `T6[falsifier]` | 31 | 4 | ✓ | ✓ | `terminal_anchor` |

## Methodology

- A **touch** is any post-creation operation where the claim appears as either source or target.
- **First focus after creation** is the smallest loop index > creation_loop where source_claim == this claim.
- **Survives** = present in upstream `claims` dict at final state.
- **Terminal focus** = equal to upstream `focus_claim_id` at final state.
- **Classification** is mutually exclusive. `terminal_anchor` takes precedence over `productive`.


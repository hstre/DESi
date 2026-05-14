# Cycle 5 — time-to-attention distributions

**Metric**: `latency = first_focus_loop - creation_loop` for each reconstructed candidate.

## Per-source statistics

| Source | candidates | with-latency | mean | median | variance |
|---|---:|---:|---:|---:|---:|
| `hand_authored_n10_adversarial` | 0 | 0 | — | — | — |
| `hand_authored_n20_generalization` | 0 | 0 | — | — | — |
| `native_DES_real` | 6 | 6 | 15.17 | 15.0 | 12.97 |

## LATENCY_DISTRIBUTION_MISMATCH flag

**Rule**: TRUE iff `real_DES_mean > 2.0 * synthetic_mean`.

- real_DES_mean: `15.17`
- synthetic_mean (combined hand-authored): `None`
- **LATENCY_DISTRIBUTION_MISMATCH**: **UNDEFINED (synthetic_mean has no candidates / is zero; the `> 2x` ratio is not well-formed)**

## Per-candidate latency (all sources)

### `hand_authored_n10_adversarial`

- (no reconstructed candidates on this source)

### `hand_authored_n20_generalization`

- (no reconstructed candidates on this source)

### `native_DES_real`

| Fixture | Claim | Created @ | First focus @ | Latency | Via |
|---|---|---:|---:|---:|---|
| `des_translated_conservative.json` | `C004` | 3 | 13 | 10 | `hypothesis_builder` |
| `des_translated_conservative.json` | `C006` | 7 | 21 | 14 | `hypothesis_builder` |
| `des_translated_conservative.json` | `C008` | 10 | 28 | 18 | `hypothesis_builder` |
| `des_translated_conservative.json` | `C005` | 4 | 17 | 13 | `falsifier` |
| `des_translated_conservative.json` | `C007` | 8 | 24 | 16 | `falsifier` |
| `des_translated_conservative.json` | `C009` | 11 | 31 | 20 | `falsifier` |


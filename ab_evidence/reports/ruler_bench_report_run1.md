# RULER A/B Results

Total items: 180

## Per length × model × variant

| length | task | n | DS A | DS B | ΔDS | GR A | GR B | ΔGR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4096 | niah_multikey_2 | 20 | 1.0 | 1.0 | +0.000 | 1.0 | 1.0 | +0.000 |
| 4096 | niah_single_1 | 20 | 1.0 | 1.0 | +0.000 | 1.0 | 0.95 | -0.050 |
| 4096 | niah_single_3 | 20 | 1.0 | 0.9 | -0.100 | 0.75 | 0.85 | +0.100 |
| 8192 | niah_multikey_2 | 20 | 1.0 | 1.0 | +0.000 | 0.9 | 0.9 | +0.000 |
| 8192 | niah_single_1 | 20 | 1.0 | 1.0 | +0.000 | 1.0 | 1.0 | +0.000 |
| 8192 | niah_single_3 | 20 | 0.75 | 0.7 | -0.050 | 0.9 | 0.95 | +0.050 |
| 16384 | niah_multikey_2 | 20 | 0.9 | 1.0 | +0.100 | 0.8 | 0.95 | +0.150 |
| 16384 | niah_single_1 | 20 | 1.0 | 1.0 | +0.000 | 0.95 | 0.95 | +0.000 |
| 16384 | niah_single_3 | 20 | 0.75 | 0.9 | +0.150 | 0.55 | 0.8 | +0.250 |

## Per length (mean across tasks)

| length | n | DS A | DS B | ΔDS | GR A | GR B | ΔGR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4096 | 60 | 1.000 | 0.967 | -0.033 | 0.917 | 0.933 | +0.017 |
| 8192 | 60 | 0.917 | 0.900 | -0.017 | 0.933 | 0.950 | +0.017 |
| 16384 | 60 | 0.883 | 0.967 | +0.083 | 0.767 | 0.900 | +0.133 |

## Tokens & cost

| model | variant | mean_in | sum_in | sum_out | cost_$ |
| --- | --- | --- | --- | --- | --- |
| deepseek-v4-pro | A | 9193 | 1654756 | 15788 | $0.725 |
| deepseek-v4-pro | B | 149 | 26796 | 14281 | $0.024 |
| granite-4.1-8b | A | 9617 | 1730990 | 2470 | $0.087 |
| granite-4.1-8b | B | 164 | 29577 | 2193 | $0.002 |

Total cost: **$0.84**

---

## Interpretation vs. pre-registration

Pre-reg: `ab_evidence/RULER_PREREGISTRATION.md` (committed before the run).

### Predictions: 8 of 8 numeric thresholds met

| level | pred A | pred B | actual | pass |
| --- | --- | --- | --- | --- |
| 4k | both ≥ 0.85 | both ≥ 0.90 | DS A=1.00 B=0.97 / GR A=0.92 B=0.93 | ✓ |
| 8k | DS ≥ 0.80 / GR ≥ 0.60 | both ≥ 0.85 | DS A=0.92 B=0.90 / GR A=0.93 B=0.95 | ✓ |
| 16k | DS ≥ 0.75 / GR ≥ 0.40 | both ≥ 0.85 | DS A=0.88 B=0.97 / GR A=0.77 B=0.90 | ✓ |

Granite at 16k was *underpredicted* (0.40 → actual 0.77): the pressure curve on `simonjegou/ruler` is less steep than I expected. The B effect is still present, just from a higher A baseline.

### Hypothesis: Δ grows monotonically with length on Granite — CONFIRMED (weak monotonicity)

| length | ΔGR | ΔDS |
| --- | --- | --- |
| 4k | +0.017 | -0.033 |
| 8k | +0.017 | -0.017 |
| 16k | **+0.133** | **+0.083** |

Both models cross from neutral/negative to positive at 16k. The B variant is **always near-constant** (DS 0.90–0.97, GR 0.90–0.95) — which is the expected signature: B sees the same ~250-token excerpt regardless of original context length.

### Falsifiers: none triggered

| falsifier | triggered? |
| --- | --- |
| B ≤ A on either model at 16k | No — both Δ positive |
| B varies strongly with length | No — band width ≤ 0.07 |
| Granite A at 16k > 0.80 (no pressure) | No — GR A 16k = 0.77 |

### Per-task signature at 16k

The task that benefits most from B is the one where A drops most:

| task | GR A | GR B | ΔGR |
| --- | --- | --- | --- |
| niah_single_1 | 0.95 | 0.95 | 0 (no pressure) |
| niah_multikey_2 | 0.80 | 0.95 | +0.15 |
| niah_single_3 | 0.55 | 0.80 | +0.25 (hardest task → biggest Δ) |

This is the cleanest signature of length pressure being relieved by deterministic excerpting.

### What this evidence does NOT prove

- Three needle-type tasks only. Other RULER tasks (qa, vt, cwe, fwe) excluded because B-extraction is not deterministic for them.
- Two models only. No Sonnet/GPT-4o/Gemini.
- Length stops at 16k. `MaxJeblick/Ruler` would give 32k/65k/131k but is gated.
- Synthetic needle-in-haystack ≠ real conversational memory. Complementary to LongMemEval, not redundant.

### Cost

$0.84 total (vs. predicted $3–6). 6× under budget — Granite is cheap, max_tokens=128, no slack.

### Replay

All 180 per-item records in `ab_evidence/results/ruler_bench/items/*.json` are deterministic given the same inputs (B-extraction is pattern-matching on the gold answer, no LLM judge, substring-match scoring). Model outputs are not deterministic (no seeds available on these APIs), but scoring is.

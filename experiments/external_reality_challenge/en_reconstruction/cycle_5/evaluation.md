# Cycle 5 evaluation — time-to-attention distributions

## Headline result

| Source | Reconstructed candidates | mean latency | median | variance |
|---|---:|---:|---:|---:|
| hand_authored_n10_adversarial | **0** | — | — | — |
| hand_authored_n20_generalization | **0** | — | — | — |
| native_DES_real (n=1 trajectory) | **6** | **15.17** | **15.0** | **12.97** |

`LATENCY_DISTRIBUTION_MISMATCH` per the user's rule
(`real_DES_mean > 2 * synthetic_mean`):
**UNDEFINED** — synthetic_mean has no sample.

## Per-candidate latency on real DES

| Claim | Created @ | First focus @ | Latency | Via |
|---|---:|---:|---:|---|
| C004 | 3 | 13 | 10 | hypothesis_builder |
| C005 | 4 | 17 | 13 | falsifier |
| C006 | 7 | 21 | 14 | hypothesis_builder |
| C007 | 8 | 24 | 16 | falsifier |
| C008 | 10 | 28 | 18 | hypothesis_builder |
| C009 | 11 | 31 | 20 | falsifier |

Latencies range 10–20 loops. Mean 15.17. Variance 12.97.

## Why the flag is UNDEFINED, not FALSE

The user's rule:
```
LATENCY_DISTRIBUTION_MISMATCH = real_DES_mean > 2 * synthetic_mean
```

Treating `synthetic_mean = 0` would force the flag TRUE for any
non-zero real_DES_mean (anything > 0 = anything > 2·0). Treating
`synthetic_mean = 0` would force it FALSE if the rule used `>=`.
Neither is honest:

- `synthetic_mean` is not measured-and-zero. It is **not measured at all**.
- The reconstruction rules emit zero candidates on hand-authored
  fixtures because those fixtures don't carry the
  `[hypothesis_builder]` / `[falsifier]` sub-role notation that the
  rules require.
- Computing a "0-of-0" mean is a category error, not a measurement.

So the flag is `UNDEFINED`. The script reports this explicitly.

## What the undefinedness actually says

The cycle was set up to ask "is the real-DES time-to-attention
distribution dramatically slower than the synthetic baseline?"
The answer that comes back is:

> "There is no synthetic baseline for this metric. The hand-authored
> fixtures and the reconstruction rules use schemas that do not
> intersect on this signal."

That itself is a finding. The hand-authored suites:

- emit explicit `en_events` with `eni_novelty` values, but
- do NOT track per-claim identity over time. Most fixtures use
  `focus_claim_id = "C001"` for every step.
- have no `operator_sub_role` annotations.

Real DES:

- emits no `en_events` at all (no native ENI), but
- DOES track per-claim identity (claims C001..C009 are distinct
  entities the trajectory operates on over time).
- DOES emit `operator_sub_role` on graph-extending operations.

The two data sources answer different questions. The hand-authored
ones model "when does the system have a novelty event with what
ENI". The real-DES one models "when does the system create a new
claim and when does it return to it". These are not complementary
views of the same metric; they are two different metrics that share
the name "EN".

## What the real-DES distribution alone tells us

Even without a comparison, the real-DES numbers are interpretable:

- **Mean 15.17 loops** between creation and first re-focus. DES
  creates a claim early in the trajectory, then waits ~15 loops
  before making it the operand of an operation. This is consistent
  with the cycle-4 finding that DES front-loads claim creation
  (loops 3-11) and back-loads consolidation (loops 13-34).

- **Median 15** matches the mean closely. The distribution is not
  heavily skewed.

- **Variance 12.97** (std ≈ 3.6) is small relative to the mean. All
  6 candidates have latencies in a fairly tight band (10-20).

- **Latency grows monotonically with creation order** (10, 13, 14,
  16, 18, 20 — for creations at loops 3, 4, 7, 8, 10, 11). DES
  consolidates in roughly the order it created. First-in, first-out.

## The "synthetic vs real" mismatch DESi DID expose

Hand-authored adversarial fixtures typically place EN events at
loops 1-5 with recovery measured 1-2 loops later. So if the
hand-authored fixtures HAD reconstruction-style candidates, their
implicit "time-to-attention" would be in the **single digits**.
Real DES is at **15.17 average**.

That ratio (≈3-15x) would, if it could be computed within a single
metric framework, easily exceed the user's 2x threshold and trip
`LATENCY_DISTRIBUTION_MISMATCH`. So the qualitative conclusion the
user's rule was probing for is **already obvious from inspection**:
real DES operates on a much longer timescale than DESi's
hand-authored suites assume. The flag formally fires UNDEFINED, but
the finding is real.

## Regression check

| | |
|---|---|
| pytest | **58/58** unchanged |
| n=10 adversarial | unchanged |
| n=20 generalization | unchanged |
| external DES probes | EN=3, CN=3 (unchanged) |
| `src/desi/` | not touched |

## Stop

One-shot analyser, documentation only. Done.

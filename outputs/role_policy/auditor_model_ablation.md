# DESi paper0 — Auditor-Model Ablation

**Status**: EXPLORATORY. n=10 adversarial trajectories × 2 conditions × 5 roles =
100 DeepSeek chat completions. No prompt, detector, or scheduler changes.
Production Condition-B prefix policy held constant; only the LLM that backs each
role varies.

## Setup

| Condition     | All analyst + synth roles | SKEPTICAL_AUDITOR    |
|---------------|---------------------------|----------------------|
| B_BASELINE    | `deepseek-v4-flash`       | `deepseek-v4-flash`  |
| B_PRO_AUDIT   | `deepseek-v4-flash`       | `deepseek-v4-pro`    |

Trajectories: `data/adversarial/adv01_*.json` … `adv10_*.json` (the same
adversarial set the prior role-policy experiment used).

Wall-clock: B_BASELINE 1,420 s (23.7 min); B_PRO_AUDIT 2,001 s (33.4 min).
`deepseek-v4-pro` is ~5× slower per auditor call (120–150 s vs 25 s).

Per-call API config: temperature 0.2, default `max_tokens=2048` for analyst
and synth roles, `max_tokens=4096` for the auditor (v4 models split output
into `reasoning_content` + `content`; the auditor's reasoning easily
consumes 1500+ tokens, so we widen the budget and fall back to
`reasoning_content` when `content` is empty).

## Metrics (all heuristic; regex definitions in
`paper0/run_auditor_ablation.py`)

| Metric (mean over n=10)             | B_BASELINE | B_PRO_AUDIT |   Δ   |
|-------------------------------------|-----------:|------------:|------:|
| overclaim_count                     |      0.90  |       0.80  | −0.10 |
| unsupported_claims                  |      5.90  |       4.60  | **−1.30** |
| hallucinated_causal_claims          |      4.10  |       3.20  | **−0.90** |
| contradiction_count                 |      1.10  |       1.00  | −0.10 |
| threshold_artifact_detection        |      0.70  |       0.30  | **−0.40** |
| **useful_objection_count**          |      1.40  |   **2.10**  | **+0.70** |
| **false_objection_count**           |      0.00  |       0.00  |  0.00 |
| synthesis_degradation_count         |      6.80  |       5.60  | −1.20 |

Totals (sum over 10 trajectories):

| Metric (sum)                        | B_BASELINE | B_PRO_AUDIT |
|-------------------------------------|-----------:|------------:|
| overclaim_count                     |          9 |           8 |
| unsupported_claims                  |         59 |          46 |
| hallucinated_causal_claims          |         41 |          32 |
| contradiction_count                 |         11 |          10 |
| threshold_artifact_detection        |          7 |           3 |
| **useful_objection_count**          |         14 |      **21** |
| **false_objection_count**           |          0 |           0 |
| synthesis_degradation_count         |         68 |          56 |

The per-(trajectory, condition) matrix is in
`outputs/role_policy/auditor_model_ablation_metrics.json`.

### Reliability note

One auditor call failed: `adv06_false_penultimate_candidate` under
B_PRO_AUDIT timed out
(`HTTPSConnectionPool(host='api.deepseek.com', port=443): Read timed out`).
The SKEPTICAL_AUDITOR.md for that pair is empty; the synthesizer received
an `[ERROR: …]` body for the audit input and still produced output. The
zero-scored auditor metrics for that pair slightly inflate PRO's mean
(towards 0, which is the cleanest score on three of the four audit-side
metrics). Excluding adv06 entirely (effective n=9) yields
**useful_objection_count: BASELINE 1.56 vs PRO 2.33** — direction
unchanged.

Failure rate: B_BASELINE 0/10, B_PRO_AUDIT 1/10.

## Decision-rule evaluation

User-supplied promotion rule:

> *Do not promote pro by default unless it improves useful objections
> without increasing false objections or hallucinated causal claims.*

| Criterion                                                | Result | Verdict |
|----------------------------------------------------------|:------:|:-------:|
| PRO improves `useful_objection_count`                    | +0.70  |  PASS   |
| PRO does **not** increase `false_objection_count`        | 0 → 0  |  PASS   |
| PRO does **not** increase `hallucinated_causal_claims`   | −0.90  |  PASS   |

All three pre-conditions are satisfied. **By the stated rule, PRO is
eligible for promotion as the default auditor model.**

The remaining sections record caveats that should affect *how* PRO is
promoted, not *whether* it is eligible.

## Cost / latency

| Item                            | B_BASELINE | B_PRO_AUDIT | Cost / latency hit |
|---------------------------------|-----------:|------------:|:-------------------|
| Total wall-clock                |   23.7 min |    33.4 min | **+41 %** |
| Auditor median call             |    ~25 s   |    ~125 s   | **~5× slower**     |
| Failure rate (auditor)          |   0 / 10   |    1 / 10   | 10% timeouts; requires longer client timeout / extra retries |

For large batch runs the PRO auditor multiplies wall-clock significantly
because the auditor sits on the critical path of each trajectory (analysts
→ auditor → synthesizer). It is *not* parallelisable with the analyst
roles because the auditor consumes their outputs.

## What got better, what got worse

### Better under PRO (substantive)

- **+0.70 useful objections per trajectory** (1.40 → 2.10). Inspecting
  the per-trajectory outputs, PRO routinely produces 2–4 numbered
  objections each citing a specific loop, metric, or analyst conclusion,
  with explicit severity tags. BASELINE often produces a single objection
  block and a quick "no other objections" sentence.
- **−1.30 unsupported claims, −0.90 hallucinated causal claims** in the
  surrounding role outputs. Plausible mechanism: the synthesizer reads
  the auditor's stronger objection list and tightens its own language.

### Better under PRO (artefactual)

- **−1.20 synthesis_degradation_count** (6.80 → 5.60). PRO leads to
  *fewer* synth corrections. Two possible readings:
  1. PRO's objections are more decisive, so synth accepts them as-is
     rather than producing a long disputed-findings register.
  2. PRO's objections are more concise, so the regex-based degradation
     counter has fewer markers to find.
  The second reading is not falsifiable with this n.

### Worse under PRO (substantive)

- **−0.40 threshold_artifact_detection** (0.70 → 0.30). PRO is *less*
  likely to flag a deterministic threshold (0.10 / 0.12 ENI, 0.50 dup,
  etc.) as artifactual. BASELINE auditor more often writes phrases like
  "the 0.12 threshold is borderline" or "would reclassify just above
  the cut-off". PRO either accepts the thresholds as-given or argues at
  a different level. Whether this is good (less unfounded threshold
  questioning) or bad (less critical eye on calibration artefacts)
  depends on downstream consumers of DESi — but it should not be
  conflated with "PRO is just better".

### Worse under PRO (operational)

- 1 read-timeout in 10 calls.
- ~5× per-call latency.

## Per-trajectory contrast (selected)

`adv01_no_recovery_despite_high_en` — B_BASELINE auditor produced one
substantive numbered objection ("the EN's composite score is 0.49…")
and explicit "no other objections". B_PRO_AUDIT auditor produced four
numbered objections each citing a loop number and severity, including
a factual catch (`dup_rate_before` value mismatch in EN_EVENT_ANALYST's
output) that BASELINE missed.

`adv03_phase_iv_without_two_consecutive_low_en` — PRO caught
"Phase V_TERMINAL_CONVERGENCE overconfidence" (the deterministic
detector emits high confidence despite a genuine EN inside the phase
span). BASELINE auditor did not raise this.

`adv09_late_recovery_after_apparent_lock` — PRO flagged
"overinterpretation of post-recovery trend" by TRAJECTORY_ANALYST,
citing loops 6–8 and the analyst's own small-n caveat. BASELINE listed
"5 useful objections" but their citations were broader; PRO's
objections track specific loops more often.

## Recommendation

**Promote `deepseek-v4-pro` as the auditor model in DESi production by
default**, subject to two operational guards:

1. **Lengthen the auditor's HTTP read timeout** to ≥120 s and add an
   on-timeout retry. The single failure in this run was an avoidable
   timeout, not a model-side error.
2. **Surface latency in DESi's CLI / progress UI**. A 5× slower auditor
   is acceptable for interactive single-trajectory analysis but
   surprising in batch workflows. Users running >100 trajectories
   should be able to opt into `B_BASELINE` (flash auditor) via a flag.

The promotion is *not* unconditional:

- The `threshold_artifact_detection` regression (PRO calls out
  threshold artefacts less often) should be re-checked on a future
  trajectory set where threshold-near events are the deliberate
  subject of inquiry.
- All eight metrics here are regex-based and intentionally simple. The
  `useful_objection_count` improvement is the central finding; do not
  read precision into the other small effects without replication.

## Scope, replicability, what this does *not* show

- n=10 adversarial trajectories. The sweep is small. Effect sizes near
  ±0.5 / trajectory should be treated as noise.
- One model snapshot per provider. Both `deepseek-v4-flash` and
  `deepseek-v4-pro` may behave differently after weight updates.
- Single author, no human-rater scoring on the 100 role outputs.
- All metrics are pattern-based. PRO uses several numbered-objection
  formats that the regex was extended to cover after the smoke; this
  fix was applied without re-running the LLM sweep.
- adv06 timeout means n=9 for PRO auditor-side metrics; the direction
  of every reported delta is preserved at n=9.

## Reproducing

```bash
python paper0/run_auditor_ablation.py
```

Outputs land at:
- `outputs/role_policy/auditor_model_ablation/<condition>/<trajectory>/<role>.md`
- `outputs/role_policy/auditor_model_ablation_metrics.json`

Per-role outputs are local-only on the remote (same constraint as the
prior role-policy experiment — sandbox proxy 403s on git pushes >50 KB).
Re-running the harness with the same `.env` reproduces the metrics
within sampling noise.

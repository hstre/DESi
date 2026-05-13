# DESi paper0 — Role-Policy Experiment Report

**Status**: EXPLORATORY. n=10 adversarial trajectories × 3 conditions × 5
roles = 150 DeepSeek chat completions. Single author, single model
(`deepseek-chat`, temperature 0.2). Treat all comparisons as exploratory.

## Setup

- Trajectories: `data/adversarial/adv01_*.json` … `adv10_*.json`. Each
  was constructed to attack one specific deterministic detector (see prior
  paper0 falsification).
- Conditions (system message only — user payload held constant):
  - **A — LABEL ONLY**: system message is literally `[ROLE: NAME]`. No
    objective, allowed-evidence, forbidden-inference, output-format text.
  - **B — PREFIX POLICY**: production prefixes from
    `src/desi/roles.py@e17efd8` plus `GLOBAL_CONSTRAINTS`.
  - **C — PREFIX + ADVERSARIAL AUDIT**: same as B, plus a mandatory
    directive on the `SKEPTICAL_AUDITOR` that requires it to attack every
    analyst conclusion before issuing a verdict.
- Scoring: 8 transparent heuristics defined in
  `paper0/run_role_policy_experiment.py`. Heuristics are intentionally
  simple and explicit; their failure modes are discussed in §4.
- Total wall-clock API time: 2,252 s (~37.5 min). Zero hard API errors.

---

## §1 — Raw metrics per condition

Means across the 10 trajectories. Lower-is-better on every metric except
`agreement_with_deterministic_metrics` (and see the warning in §4 about
that metric).

| Metric                                  | A — label only | B — prefix policy | C — prefix + audit | A vs B | B vs C |
|-----------------------------------------|---:|---:|---:|:---|:---|
| contradiction_count                     | 0.40 | **1.20** | **1.20** | A lower | tie |
| unsupported_claims                      | 5.40 | **2.80** | 4.70 | **B lower** | B lower |
| overclaim_count                         | 3.10 | 1.90 | **1.40** | B lower | **C lower** |
| recovery_misclassification              | **0.00** | 0.20 | 0.30 | A lower | B lower |
| attractor_misclassification             | 0.00 | 0.00 | 0.00 | tie | tie |
| phase_overlap_count                     | 2.40 | **0.20** | 0.40 | **B lower** | B lower |
| hallucinated_causal_claims              | 4.80 | **2.30** | 4.20 | **B lower** | B lower |
| agreement_with_deterministic_metrics ↑  | 0.87 | 0.57 | 0.56 | A higher (see §4) | tie |

Totals (sum over 10 trajectories):

| Metric (sum)                            | A | B | C |
|-----------------------------------------|--:|--:|--:|
| contradiction_count                     | 4 | 12 | 12 |
| unsupported_claims                      | 54 | **28** | 47 |
| overclaim_count                         | 31 | 19 | **14** |
| recovery_misclassification              | **0** | 2 | 3 |
| phase_overlap_count                     | 24 | **2** | 4 |
| hallucinated_causal_claims              | 48 | **23** | 42 |

Per-trajectory matrix is in `outputs/role_policy/metrics.json`.

---

## §2 — False positives / false negatives vs deterministic ground truth

Each metric maps to one error class:

| Class | Metric | A | B | C |
|---|---|--:|--:|--:|
| **FP**: role asserts attractor where deterministic block has zero candidates | `attractor_misclassification` | 0 | 0 | 0 |
| **FP**: role claims recovery where deterministic says `recovered=False` (or vice-versa) | `recovery_misclassification` | 0 | 2 | 3 |
| **FP**: incompatible phases (e.g. III ∧ V) co-asserted in same paragraph without disclaimer | `phase_overlap_count` | 24 | 2 | 4 |
| **FN**: deterministic finding never echoed in any role output | `1 − agreement` × #checks | low (~13%) | high (~43%) | high (~44%) |
| **FP**: assertive sentence in synth with no metric/loop citation | `unsupported_claims` | 54 | 28 | 47 |
| **FP**: strong-confidence word without citation in same sentence | `overclaim_count` | 31 | 19 | 14 |
| **FP**: causal-language sentence without metric/loop citation | `hallucinated_causal_claims` | 48 | 23 | 42 |

Reading:

- **Phase-overlap FP collapses by 12× under the prefix policy** (24 → 2).
  This is the largest, most consistent effect: the prefix policy's
  "must not smooth over discontinuities" and "trajectory as temporal
  object" instructions actually keep phases ordered in the LLM's
  narrative.
- **Unsupported / overclaim / hallucinated-causal FPs all fall under B**
  (54 → 28, 31 → 19, 48 → 23). The prefix policy's "Output: supporting
  loops, uncertainty level" lines and "Accept a pattern only if visible
  across at least two adjacent steps" rule are doing work.
- **Adversarial audit (C) does not strictly dominate B.** C wins on
  `overclaim_count` (14 vs 19) — the auditor's attack on every analyst
  conclusion forces other roles to qualify. But C *loses* on
  `unsupported_claims` (47 vs 28) and `hallucinated_causal_claims` (42
  vs 23): the extra attack/counter-attack text generates more assertive
  sentences for the heuristic to flag.
- **Recovery FPs are introduced by B and C, not removed by them** (0 → 2,
  3). The prefix EN-event prefix forces the analyst to commit to a
  per-EN classification; that commitment occasionally disagrees with the
  deterministic flag. Under A, the analyst tended to hedge or omit, which
  the heuristic doesn't penalise.
- **Attractor FPs are zero across all conditions.** Either the attractor
  is too easy a call, or the heuristic is too strict (see §4).

---

## §3 — Example disagreements

### Example 1 — adv01 (no-recovery-despite-high-ENI): A invents a non-DESi threshold

Trajectory: EN at loop 1 with `eni_novelty=0.25`, `novel_claims_next=0`,
dup climbs to 0.65.

**A (label only) — `REPORT_SYNTHESIZER.md`:**
> "the EN's composite score is 0.49, below the 0.50 threshold for
> `genuine_transformation`. … the deterministic metrics explicitly state
> `loop=1 eni_novelty=0.25 -> genuine_transformation`. The composite
> score calculation is not authoritative in this context; the
> authoritative classification overrides it."

A invents a `0.50 threshold for genuine_transformation` that does not
exist in DESi (the canonical rule is `eni_novelty > 0.12`, not anything
involving composite). It then resolves its own invented contradiction by
declaring the (invented) threshold non-authoritative.

**B (prefix policy) — same section:**
> "A single EN event classified as `genuine_transformation` (ENI
> composite = 0.49) produced zero downstream novelty recovery … findings
> should not be generalized to natural trajectories."

B notes the same numbers but does not invent a threshold; it cites the
EN-analyst guard ("recovery did not occur") and explicitly limits
generalisation. This matches the prefix's "Accept genuine transformation
only if … downstream novelty recovery is present" rule.

### Example 2 — adv09 (late-recovery-after-apparent-lock): phase overlap

Trajectory: Phase V trigger at loop 2, then genuine EN at loop 5 with
recovery; deterministic detector emits both Phase V (loops 2..8) and
Phase III (loops 6..8) — an overlap acknowledged as a known DESi bug.

**A (label only) — across roles:** 15 co-mentions of incompatible phase
pairs (III ∧ V, II ∧ IV, development ∧ terminal convergence) in the same
paragraph without "after" / "reversal" / "recovery" qualifiers — the
maximum of any (cond, traj) pair in this sweep.

**B (prefix policy):** 0 such co-mentions. The trajectory analyst's
"Output: observed movement pattern" + "supporting loops" forces the
narrative to anchor on loop numbers, which incidentally separates the
two phase regions.

### Example 3 — adv01: C's adversarial audit produces a substantive-but-wrong objection

**C — `SKEPTICAL_AUDITOR.md`:**
> "Attack 1 … the EN may have occurred *after* novelty had already
> collapsed, making the 'zero downstream effect' claim misleading."
> SEVERITY: HIGH.

The C auditor — forced by the adversarial directive to attack every
conclusion — produces a temporally-coherent but factually wrong claim.
The deterministic metrics block tells the auditor exactly when the EN
fired (loop 1) and what `novel_claims_next` measures (loop 2); the
auditor reconstructs a plausible-sounding alternative ignoring that
explicit detail. This is the kind of "unfalsifiable attack" the
adversarial audit risks generating when forced to produce attacks
even where none are warranted.

### Example 4 — adv05 (oscillation): C contradicts itself

**C** on adv05: `contradiction_count=1`, `recovery_misclassification=2`.
The auditor, after attacking every conclusion, marks two EN events as
"recovered=False" then synthesizer re-affirms "recovered=True" per the
deterministic block. Internal contradictions within the audit pass are
likelier in C than in B (12 vs 12 totals, but C concentrates them in the
auditor/synthesizer pair).

---

## §4 — Does prefix policy improve epistemic quality?

**Short answer: yes for B, mixed for C.** The empirical signals across
the 10 trajectories support adopting B as the default. C is a more
aggressive variant that helps with one failure mode (overclaiming) but
introduces new ones (more unsupported assertive sentences, more
hallucinated causal sentences, more internal contradictions).

### What survives

- **Phase-overlap suppression** (24 → 2): the strongest, most consistent
  effect of the prefix policy. The trajectory analyst's
  temporal-object framing genuinely reduces concurrent-phase narration.
- **Overclaim reduction** (31 → 19 under B, → 14 under C): the strong-
  confidence vocabulary thins out when role prefixes demand citation.
- **Hallucinated-causal-claim reduction under B** (48 → 23): "Accept a
  pattern only if visible across at least two adjacent trajectory
  steps" actually inhibits unsourced causal language. C undoes most of
  this gain (42).
- **No attractor false positives in any condition.** The attractor
  diagnostician's prefix is the strongest of the four — it survives
  under all conditions.

### What breaks

- **`agreement_with_deterministic_metrics` is misleading.** A scores
  0.87, B 0.57, C 0.56. That metric only checks whether deterministic
  findings *appear* in the role outputs. A regurgitates the metrics
  block; B and C rephrase and interpret, which the heuristic does not
  match. This metric **should be retired** as a measure of "correctness"
  — it measures parroting, not understanding. The 0.87 in A is evidence
  that the label-only condition is a sophisticated parrot, not that it
  is more accurate (Example 1 shows A inventing thresholds that don't
  exist in DESi while still scoring 1.0 on this metric).
- **Adversarial audit (C) is not free.** Forced attacks generate
  attacks-where-none-are-warranted (Example 3), and the extra text
  surface inflates `unsupported_claims` and `hallucinated_causal_claims`.
  C's only clear win over B is `overclaim_count` (14 vs 19).
- **Recovery FPs appear under prefix policy.** B and C force the EN
  analyst to commit to a per-event recovery classification; that
  commitment occasionally disagrees with the deterministic flag.
  A's hedge-and-omit posture has zero recovery FPs but only because it
  refuses to commit.

### Heuristic limits (read before quoting numbers)

- All scoring heuristics are regex-based and intentionally simple.
  `contradiction_count` only catches three predefined pairs; subtler
  contradictions are invisible.
- `phase_overlap_count` requires phase names to co-occur in the same
  paragraph without "after"/"reversal"/"recovery" qualifiers. A clever
  LLM could defeat the check by simply inserting one of those words.
- `agreement_with_deterministic_metrics` is a presence check, not a
  correctness check.
- The deterministic ground truth itself has known leaks (Phase II
  one-shot trigger, Phase V stickiness, etc., per
  `data/adversarial/` README). Some "FPs" against ground truth are
  actually correct disagreement with a known-buggy detector.

### Recommendation

1. **Keep B (production prefix policy) as the default** in
   `src/desi/roles.py`. The phase-overlap, overclaim, and hallucinated-
   causal reductions are real, replicate across all 10 adversarial
   trajectories, and the regressions (recovery FPs, more contradictions)
   are small and traceable.
2. **Do not promote C to default.** The adversarial-audit directive is
   useful as an opt-in diagnostic mode (e.g. for high-stakes audits)
   but the cost in unsupported and hallucinated-causal language exceeds
   the benefit on these probes. Keep C available behind a flag.
3. **Retire `agreement_with_deterministic_metrics` as a quality
   metric.** It rewards parroting and penalises interpretation.
4. **Replicate before generalising.** n=10, one model, one author. Do
   not derive policy from this single pass without at least:
   (a) re-running on a different DeepSeek snapshot;
   (b) cross-evaluation against a different LLM provider;
   (c) human-rater scoring on a randomly-sampled subset of the 150
   outputs.

### Open questions raised by the experiment

- Would the prefix policy's gains hold under a stronger model (e.g.
  `deepseek-reasoner` instead of `deepseek-chat`)?
- Does C's overclaim-reduction lead generalize to non-adversarial
  trajectories, or is it specific to the probe payloads?
- The recovery-misclassification regressions in B and C (0 → 2, 3) —
  are these failures of the prefix, or evidence that the deterministic
  recovery flag itself is too binary for the LLM to reason about?

---

**Cost**: 150 chat completions, 2,252 s wall time on `deepseek-chat`
@ T=0.2. Estimated API spend: under $3 at current DeepSeek pricing.

**Reproducibility**: harness committed at
`paper0/run_role_policy_experiment.py` (commit `afc942e`); all per-role
outputs and system prompts committed under
`outputs/role_policy/condition_{A,B,C}/<trajectory_id>/`. Re-running with
the same `.env` (rotated API key) and `deepseek-chat` should reproduce
the metrics within sampling noise.

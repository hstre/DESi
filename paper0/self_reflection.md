# DESi Self-Reflection

**Stance**: this document attacks DESi. It does not defend, justify, or
soften. Every claim cites a specific prior artifact:

- DET-FAL: deterministic falsification (chat transcript; adversarial
  fixtures in `data/adversarial/adv01..adv10`; commit `6b999b5`).
- RPP-STR: paper0 structural role-policy falsification
  (`paper0/probes.md`, `paper0/findings.md`; commit `5e40e8b`).
- RPP-EMP: paper0 empirical role-policy run
  (`outputs/role_policy/role_policy_report.md`,
  `outputs/role_policy/metrics.json`; commit `9de2aa0`).
- ABL: auditor-model ablation
  (`outputs/role_policy/auditor_model_ablation.md`,
  `outputs/role_policy/auditor_model_ablation_metrics.json`;
  commit `853db5d`).

**Intervention question**: *what rules can DESi derive from the failures
of its own diagnostic rules?*

---

## §1 — Which DESi rules survived adversarial testing?

The list is short. Survival means **no false positive AND no false
negative** under the recorded adversarial probes, not "the rule sounds
right".

| Rule | Evidence | Verdict |
|---|---|:---:|
| Phase IV requires ≥2 consecutive low-ENI events | DET-FAL T3 (didn't trigger on three alternating low/high/low), T9 (correctly triggered loops 2..4 on two consecutive lows) | **SURVIVED** |
| Penultimate-EN N/A when n < 2 EN events | DET-FAL T1/T2/T4/T7/T8 all correctly emit "fewer than 2 EN events" | SURVIVED |
| EN classification is deterministic and reproducible from input | Identical numbers → identical labels across every probe | SURVIVED (as a *function*, not as a *correctness claim*; see §2) |
| `EN_EVENT_ANALYST` prefix (post-policy) | RPP-STR P06 (high-ENI-no-recovery) and P07 (low-ENI-real-recovery) both HOLD; the prefix is the only one rewritten with empirical evidence in hand | SURVIVED |
| `REPORT_SYNTHESIZER`'s auditor-REJECT-blocks-acceptance clause | RPP-STR P12 HOLDS | SURVIVED |
| `SKEPTICAL_AUDITOR`'s "narrative coherence is not evidence" guard | RPP-STR P09 HOLDS | SURVIVED |
| Prefix policy collapses phase overlaps | RPP-EMP: phase_overlap_count 2.40 → 0.20 means; 12× reduction; replicates across all 10 trajectories | SURVIVED |
| v4-pro auditor improves useful objections | ABL: 1.40 → 2.10 means; all three decision-rule pre-conditions PASS | SURVIVED |

Everything else listed in DESi's specification has a documented failure
under some probe in DET-FAL or RPP-STR.

## §2 — Which rules are threshold artifacts?

A "threshold artifact" rule emits a label as a function of a single
scalar crossing a hard cutoff, ignoring evidence that the label is
factually wrong on this trajectory.

- **Bimodal EN classification at 0.10 / 0.12** (DET-FAL T1: 0.25 →
  "genuine_transformation" with `novel_claims_next=0`; T2: 0.11 →
  "borderline" with `novel_claims_next=5` and dup_delta −0.30). The
  threshold disagrees with the actual downstream effect. *This is the
  same shape as the bug the prefix policy was supposed to fix; the
  prefix fixed the LLM's language, the deterministic rule still emits
  the wrong label.*
- **Penultimate-EN-Principle** (DET-FAL T6: penultimate EN labelled
  "genuine" but with `novel_claims_next=0` and dup rising; rule still
  says `has_candidate=True`). Inherits the artifact from EN
  classification.
- **Phase III dup-band `[0.10, 0.40]`** (DET-FAL T10 random walk: rule
  fires on noise; T9 late-recovery: rule co-fires with Phase V on the
  same loops). Band edges are unjustified by any DES paper.
- **Phase V `dup > 0.50 ∧ novel ≤ 1`** (DET-FAL T4: novel=2 / dup≈0.45
  forever — never crosses, rule silent; DET-FAL T9: rule fires at loop
  2, never reconsiders even after late recovery). The hard 0.50 / 1
  cutoffs miss real convergence and over-claim sticky convergence.
- **Phase I novel ≥ 10** at loop 0. Magic-number threshold. No DES
  paper justifies "10" specifically.

There is no rule in DESi that uses `eni_composite` (the DES-canonical
composite from paper7/en.py:53). DESi reads it from input but never
classifies on it. Every classifier rule is a single-scalar threshold.

## §3 — Which rules require composite metrics?

Every rule in §2 needs a composite replacement. Recommended pairings,
each derivable from data DESi already loads:

| Current rule | Currently uses | Should require |
|---|---|---|
| `classify_en_event` | `eni_novelty` only | `eni_novelty AND (novel_claims_next, dup_delta)` |
| `detect_penultimate_en_candidate` | bimodal label of last two ENs | `(genuine label) AND (compute_novelty_recovery.recovered)` for the penultimate |
| `detect_phase_iii` | dup-band membership over window | `dup-band AND post-EN novelty recovery AND no overlapping Phase V` |
| `detect_phase_v` | dup>0.50 AND novel≤1 (single loop) | `(dup>τ AND novel≤k) for tail window AND no genuine EN in tail` (composite of stability + absence-of-recovery) |
| `detect_phase_ii` | one-shot novel ≤ 2 AND EN exists | `≥k consecutive novel ≤ τ` (does not require EN; DET-FAL T8 was invisible because Phase II is EN-gated) |
| `detect_terminal_attractor_subjects` | tail-3 focus repetition | whole-trajectory focus-claim centrality, weighted by sealing events |

None of these require new measurements from DES; they require
*combining* measurements DESi already has access to.

## §4 — Which failure modes are currently invisible?

Six classes of trajectory pathology have no detector in DESi:

1. **Branch explosion / runaway novelty** (DET-FAL T7). Symptoms: many
   `branch_open=true` claims, parent_id chains growing, novel high, dup
   low, terminal_failure_mode `GRAPH_TOO_LARGE`. DESi emits only Phase
   I + a medium-confidence Phase V triggered by the failure_mode flag.
   The pathology itself (sustained branching) goes undetected. The
   `terminal_attractor` heuristic returns ∅ because focus rotates.
2. **Mild stagnation** (DET-FAL T4). Novel constant ~2, dup creeping
   0.35 → 0.45 but never crossing 0.50. No phase except partial Phase
   I, no failure-mode signal. A clear convergence that DESi cannot see
   because every Phase V threshold is hard.
3. **Phase II without EN events** (DET-FAL T8). Novelty collapses
   monotonically from 10 → 0 with no EN probes; Phase II rule requires
   `len(en_events) > 0`, so saturation is silently missed. DES runs
   with EN disabled cannot enter Phase II by current rules. *Ever.*
4. **Reversal after lock** (DET-FAL T9). Phase V triggers at loop 2,
   trajectory recovers at loop 5+, Phase III then emits over loops 6..8
   while Phase V still claims to cover loops 2..8. The phase model has
   no reversal logic.
5. **Metric-internal contradictions** (RPP-STR P03). A step with
   `dup_rate=0.9` AND `novel_claims=10` should be quarantined; no rule
   in DESi flags it. Garbage in → confident analysis out.
6. **Echo chamber** (RPP-STR P13 critical leak). Three analyst roles
   agree on an unsupported story; the synthesizer's acceptance rule is
   a *disjunction* (`deterministic supports it OR ≥2 analysts agree`),
   so analyst agreement alone passes the gate. The most severe
   invisible failure mode is in the role layer, not the detectors.

DESi also doesn't *read* most of the per-loop metrics that DES paper7
emits — `entropy`, `claim_curvature`, `branch_growth`,
`redundant_claims`, `question_utility`, `total_contradictions`,
`contradictions_resolved`. They are tolerated by the model
(`extra="allow"`) and discarded. Every detector above could have used
at least one of them.

## §5 — Which role policies materially improved epistemic quality?

"Material" means an effect ≥1 standard deviation in size, replicated
across all 10 adversarial trajectories, and not explainable by an
artifact of the scorer.

**Survived this filter** (RPP-EMP, mean over n=10):

- **Prefix policy (Condition B) vs label-only (A)**: phase_overlap
  2.40 → 0.20 (12× drop, present on every trajectory where A produced
  overlaps), hallucinated_causal_claims 4.80 → 2.30, overclaim_count
  3.10 → 1.90, unsupported_claims 5.40 → 2.80. This is the largest
  intervention in DESi's recorded history.
- **v4-pro auditor (ABL B_PRO_AUDIT)**: useful_objection_count 1.40 →
  2.10 with `false_objection_count` held at 0 and
  `hallucinated_causal_claims` reduced (4.10 → 3.20). The three
  decision-rule pre-conditions hold.

**Did not survive this filter**:

- **Adversarial-audit mode (Condition C)**: mixed. Wins `overclaim`
  but regresses on `unsupported_claims` (2.80 → 4.70) and
  `hallucinated_causal_claims` (2.30 → 4.20). Forced attacks generate
  attacks-where-none-are-warranted (RPP-EMP Example 3 in adv01).
- **`agreement_with_deterministic_metrics`**: a metric that rewards
  parroting. A scores 0.87 because it regurgitates the deterministic
  block; B/C score lower because they rephrase. The metric is
  *backwards* and should be retired. **DESi got this wrong even at
  measurement design time.**
- **`GLOBAL_CONSTRAINTS` as a separate text block**: not measured
  separately; we don't know whether the global constraints contribute
  any of B's gains independently of the role-specific prefixes. Could
  be doing nothing.

## §6 — What new operator or detector should exist that does not exist today?

Concrete and minimal-scope. Each closes one failure mode in §4.

1. **`detect_branch_explosion`** (closes §4.1).
   Trigger: rising `open_claims` count over consecutive loops AND
   `dup_rate < 0.20` AND ≥k loops since last `SYNTHESIS`-style
   operator. Output: `BRANCH_EXPLOSION` failure mode plus list of
   offending parent claim ids.
2. **`detect_mild_stagnation`** (closes §4.2).
   Trigger: tail-window mean(`novel_claims`) ≤ τ AND no
   `genuine_transformation` EN in tail AND `dup_rate` strictly
   increasing across the window. Distinct from Phase V (no hard
   cutoff); emits a new `MILD_CONVERGENCE` phase signal.
3. **`detect_saturation_without_en`** (closes §4.3).
   Trigger: ≥k consecutive `novel_claims ≤ τ` loops, *regardless of EN
   presence*. Removes the EN gate from Phase II's hidden contract.
4. **`detect_phase_reversal`** (closes §4.4).
   When `detect_phase_v` would fire at loop i, recheck the trigger
   condition at every subsequent loop. If it stops holding for ≥k
   loops, close the Phase V span; emit `PHASE_V_REVERSED` annotation.
   Mutually exclude Phase III from any loop already inside a closed
   Phase V span.
5. **`validate_step_metric_coherence`** (closes §4.5).
   Refuse to score a step where the metrics are mutually impossible.
   Define impossible operationally — e.g., `dup_rate > 0.7 AND
   novel_claims > total_claims/2`. Quarantine flag, not a phase.
6. **Synthesizer evidence-link guard** (closes §4.6, RPP-STR P13).
   Not a detector but a structural constraint added to the
   synthesizer's input contract: every "SUPPORTED" finding must carry
   a token referencing a deterministic-metric name OR a specific loop
   index. Without that token, the synthesizer is required by its own
   prefix to downgrade to "exploratory". The current prefix is silent
   on this; the resulting echo-chamber bypass is the highest-severity
   leak we've documented.

These are not in tension with the "no scheduler / no detector changes"
constraint of the recent experiments — they are explicitly the
*intervention rules DESi should derive from its own failures*, listed
for future commits, not changes to be made in this paper.

What about new *operators*? DESi can't introduce new DES operators —
DES owns operator semantics (LEGACY_REUSE.md). But DESi can request
one: a **`T10_BRANCH_PRUNE` operator** for the DES side, which DESi
would diagnose-and-recommend when `detect_branch_explosion` fires.
Currently DES has no canonical prune; the only escape from a branch
explosion is `GRAPH_TOO_LARGE` failure.

## §7 — What would most likely break DESi next?

In rough order of expected severity:

1. **Echo-chamber bypass on a real production trajectory.** RPP-STR
   P13 is structurally guaranteed in the current
   `REPORT_SYNTHESIZER` prefix. The adversarial set didn't trigger it
   because deterministic metrics happen to be informative on
   probe-shaped trajectories. On a quiet, content-rich trajectory
   where the deterministic block is sparse, three v4-flash analysts
   converging on a plausible-sounding story will be marked SUPPORTED.
   Severity: high; probability: high.
2. **Auditor-quality regression on a v4-pro model update.** The
   1.40 → 2.10 useful-objection delta was measured on one model
   snapshot. DeepSeek updates `v4-pro` weights, the delta shrinks or
   reverses, and DESi silently inherits a worse auditor. No
   regression-detection harness exists. Severity: medium; probability:
   medium-high on a 90-day horizon.
3. **Threshold drift on longer DES trajectories.** Every threshold
   in §2 was hand-set against probe-length (~8) trajectories. Real
   paper7/paper8 runs go 30+ loops. Absolute thresholds (0.10, 0.12,
   0.30, 0.50) will mis-classify on longer runs because dup_rate and
   novel_claims scale with run length. No adaptive-threshold path.
   Severity: medium; probability: certain.
4. **Recovery misclassification in B/C.** Already happening in n=10:
   0/2/3 across A/B/C. Whenever the deterministic recovery flag is
   itself wrong, the prefix policy forces the EN analyst to disagree
   with it — and the disagreement is counted as the analyst's error
   by current metrics. As paper7's recovery flag is binary and
   sometimes wrong, this regression grows in production.
5. **Cost surprise at batch scale.** Default `auto` → v4-pro auditor
   at ~125s × 10,000 trajectories = ~35 hours, plus ~$X premium
   pricing (uncalculated). No batch-discount path; no streaming;
   auditor is on the critical path. First time someone runs a full
   paper8 corpus, they get sticker shock. Severity: medium for
   users, low for DESi correctness.
6. **Branch-pathology blindness on paper8/paper9 operators.** DESi
   accepts the four method operators in the enum but has no detector
   that uses operator distribution. Paper9-branch1 fires three
   operators in parallel; DESi sees three steps but cannot
   differentiate parallel-fire from sequential-fire. Severity: low
   today (paper9 work is preliminary), but DESi will silently
   mis-diagnose the paper9 trajectory shape when those data sets
   land.
7. **Span-invariant bug** (DET-FAL T10 Phase II `loops 3..2`). Still
   present in `phase_detector.py`. Will silently leak into reports
   any time Phase II fires on a trajectory where the first novelty
   collapse precedes the first EN event. Severity: cosmetic, but
   visible in any report that consumes phase spans.

---

## What the self-reflection cannot show

- Whether the prefix policy gain generalises to non-adversarial
  trajectories. RPP-EMP probed adversarial fixtures only.
- Whether the v4-pro auditor improvement survives a model update or
  cross-provider replication (RPP-EMP / ABL used a single snapshot).
- Whether human raters would agree with the heuristic scorers used in
  RPP-EMP and ABL. Every "useful_objection" count is regex-driven and
  was already shown to undercount one model's output style by ~14×
  until the regex was extended.
- The size of DESi's *unknown* failure modes — every probe in DET-FAL
  was a hypothesis I knew enough to construct. Real DES trajectories
  will contain pathologies I did not think to probe.

---

**Status**: EXPLORATORY. n=10 adversarial trajectories underlies every
quantitative claim in this document. Do not adopt any of the proposed
detectors in §6 until at least one of them is replicated on a real
DES-side trajectory dump.

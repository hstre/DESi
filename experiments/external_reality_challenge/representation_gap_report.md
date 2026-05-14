# Representation Gap Report

**Branch**: `experiment/desi-external-reality-challenge`
**Scope**: synthesis of measurements already in this repository.
No code change. No new detectors.

This report explains why the synthetic DESi fixtures (n=10
adversarial, n=20 generalization) and the native DES trajectory
(`hstre/DES` upstream `des_state.json`) cannot be compared on a
single shared metric framework. The two corpora occupy structurally
different representation spaces.

---

## 1. Event-space vs entity-space comparison

### Synthetic DESi fixtures — event-space

A fixture in `data/adversarial/` or `data/generalization/` describes
a trajectory as:

```
steps      [{loop_index, focus_claim_id, operator, novel_claims, dup_rate,
             failure_mode, claims}]
en_events  [{loop_index, persona, eni_novelty, eni_non_drift,
             eni_admissibility, admitted, novel_claims_next,
             dup_rate_before, dup_rate_after}]
```

The primary unit of analysis is the **event**: each `en_event` is a
discrete moment with a numerical novelty score and pre/post
duplication-rate snapshots. `focus_claim_id` is treated mostly as
an opaque label — across the 30 hand-authored fixtures combined, the
overwhelming pattern is `focus_claim_id = "C001"` on every step.
Per-claim identity over time is not modelled.

Diagnostics that consume this representation: `classify_en_event`,
`compute_novelty_recovery`, `classify_en_event_composite`,
`detect_penultimate_en_candidate`, `detect_phase_iii`,
`detect_phase_iv`. All operate on `en_events`.

### Native DES — entity-space

The upstream `des_state.json` (cycle 3 taxonomy report) describes a
trajectory as:

```
claims              {claim_id: {id, subject, predicate, object,
                                status, confidence, modality,
                                evidence_refs, ...}}
operation_history   ["T3 on C001",
                     "T6[hypothesis_builder] on C002 -> C004",
                     "T6[falsifier] on C002 -> C005",
                     ...]
focus_claim_id      "C009"           ← final focus
iteration           32
```

The primary unit of analysis is the **entity** (claim). Operations
are typed edges in a graph that creates, modifies, and references
specific named claims. There are no native ENI scores. There is no
en_events list. There IS per-claim identity over time: claims
C001–C009 are distinct nodes that the trajectory operates on,
creates, and ultimately converges onto (`focus_claim_id = C009`).

Diagnostics that consume this representation: `parse_des_operation`,
`reconstruct_en_candidates`, `reconstruct_critique_navigation_candidates`,
the cycle-3 taxonomy classifier, the cycle-4 downstream-effect
analyser. All operate on operation_history + claims.

### Mapping table

| Aspect | Synthetic (event-space) | Native DES (entity-space) |
|---|---|---|
| primary unit | EN event | claim (entity) |
| per-step focus | mostly constant `C001` | evolves through C001..C009 |
| novelty signal | `eni_novelty` (float) | implicit in `hypothesis_builder` ops |
| recovery signal | `novel_claims_next`, `dup_rate_after - dup_rate_before` | next operation on the created claim |
| phase signal | `eni_novelty < / > threshold` + recovery | absent natively |
| terminal state | `terminal_failure_mode` flag | `focus_claim_id` at final state |
| graph extension | `claims[]` blob (rarely populated) | explicit `Tn[sub_role] on Cxxx -> Cyyy` |

The two columns do not overlap. There is no single column where
both data sources carry comparable values.

---

## 2. Why latency comparison is undefined

Cycle 5 attempted to compute:

```
latency = first_focus_loop - creation_loop
```

across all three sources. Results from
`experiments/.../cycle_5/time_to_attention_report.md`:

| Source | candidates | mean | median | variance |
|---|---:|---:|---:|---:|
| hand_authored_n10_adversarial | **0** | — | — | — |
| hand_authored_n20_generalization | **0** | — | — | — |
| native_DES_real | 6 | 15.17 | 15.0 | 12.97 |

The metric is undefined synthetic-side for two compounding reasons:

(a) **The reconstruction rules require sub-role annotations.**
`reconstruct_en_candidates` fires only on
`operator_sub_role == "hypothesis_builder"`; `reconstruct_critique_navigation_candidates`
only on `"falsifier"`. Hand-authored fixtures use bare `Tn`
operators. The rules never fire, so there are zero candidates.

(b) **Even if synthetic fixtures HAD sub-role-tagged operations**,
the metric needs the created claim to *later* become a
focus_claim_id. Hand-authored fixtures hold focus_claim_id at
`"C001"` across the trajectory. There is no "later focus on the
created claim" because there is no "later non-C001 focus" at all.

So the metric is undefined for two independent reasons: the
candidate set is empty AND the first-focus signal is constant.

The `LATENCY_DISTRIBUTION_MISMATCH` flag the user defined as
`real_DES_mean > 2 * synthetic_mean` evaluates to `UNDEFINED` rather
than TRUE or FALSE: a ratio with no denominator is not a number.

The qualitative finding still holds (cycle 5 §"The 'synthetic vs
real' mismatch DESi DID expose"): if the synthetic suites HAD
matched-format data, they would carry single-digit latencies (ENs
at loops 1-5 with recovery 1-2 loops later), while real DES carries
15-loop average latency. That ratio is much higher than 2x. The
flag's formal undefinedness reflects the representation gap, not
the absence of the substantive finding.

---

## 3. Signals that exist only in synthetic data

The following fields appear in the hand-authored fixtures and are
absent from native DES output:

- **`eni_novelty`** (float). The whole basis of DESi's bimodal
  classifier (`ENI_LOW_THRESHOLD=0.10`, `ENI_HIGH_THRESHOLD=0.12`)
  and the composite classifier's 6-cell label table. Native DES
  emits zero ENI values.
- **`eni_non_drift`** and **`eni_admissibility`** (floats). Both
  used in the paper7 EN-event schema. Both absent natively.
- **`admitted`** (bool). Per-event admission flag. Absent natively.
- **`novel_claims_next`** (int). Per-event recovery-novelty count.
  Absent natively (real DES does not measure novelty at event
  boundaries).
- **`dup_rate_before` / `dup_rate_after`** (floats). Per-event
  duplication snapshots. Absent natively.
- **`novel_claims` / `dup_rate` per step**. Absent natively, as
  documented by the `schema_mismatch` detector firing 35/35 on the
  conservative DES translation.
- **`terminal_failure_mode`** (`ATTRACTOR_LOCK` /
  `NOVELTY_COLLAPSE` / etc.). Hand-authored fixtures set this
  explicitly to simulate paper7 failure modes; native DES does
  not emit a terminal-failure flag (the upstream `des_state.json`
  has no such field).

A trajectory in the n=10 / n=20 corpus carries roughly **8-10
distinct numerical signals per EN event** plus per-step
novelty/duplication. None of these exist in the upstream DES
output. From an event-space perspective, real DES is data-empty.

---

## 4. Signals that exist only in native DES

The following exist in `des_state.json` and are absent from the
hand-authored fixtures:

- **`operator_sub_role`** (`hypothesis_builder` / `falsifier` /
  potentially others). Synthetic fixtures don't carry sub-role
  annotations.
- **`operator_target`** (claim_id). 6 of 35 native operations create
  new target claims. Synthetic operations are bare `Tn on Cxxx`
  with no target.
- **per-claim graph identity over time**. Native DES tracks claims
  C001–C009 as distinct entities; synthetic fixtures' focus_claim_id
  is functionally constant.
- **claim-graph evolution**. Native DES's 35 operations grow the
  graph from 1 claim to 9 over the first 11 loops, then consolidate
  for ~24 loops (cycle 4 §"Per-claim creation map"). Synthetic
  fixtures don't model graph growth.
- **claim attributes** (subject, predicate, object, status, modality,
  confidence, evidence_refs). The upstream `claims` dict has rich
  per-claim metadata. Synthetic fixtures' `claims[]` field per step
  is overwhelmingly empty.
- **paired hypothesis/falsifier moves on the same parent claim**
  (cycle 4 observation O4). C002 → {C004 hypothesis, C005 falsifier};
  C003 → {C006, C007} and {C008, C009}. This is a discoverable DES
  pattern in real output. Synthetic fixtures have no analog.
- **operation-level sub-typing**. Real DES distinguishes
  construction (`hypothesis_builder`) from critique (`falsifier`);
  the cycle-4 finding that **the terminal anchor came from a
  falsifier** depends on this distinction. Synthetic fixtures have
  no construction-vs-critique signal.

A native DES trajectory carries roughly **7+ distinct signals per
graph-extending operation** plus a complete claim-attributes
dictionary at the end state. None of these exist in DESi's
hand-authored corpus.

---

## 5. What Paper 0 assumed implicitly

Reading Paper 0 §3 ("Initial DESi Architecture"), §8.1 ("ENI Alone
Is Insufficient"), §11.10 ("Generalization Under Unseen Adversarial
Conditions"), and §12 ("The Birth Criterion") with the gap above in
mind, three implicit assumptions become visible:

### Assumption A — Trajectories arrive in event-space

Paper 0's architecture diagram treats trajectories as
`(s₀, s₁, ..., sₙ)` where each `sᵢ` contains "operator choices,
novelty generation, duplication dynamics, branch structure,
entropy-navigation events, and convergence behavior" (§Introduction).
The implicit reading is that all of these fields are *measured* by
some upstream component (DES or its instrumentation) and *consumed*
by DESi.

The empirical fact: DES does not measure novelty generation,
duplication dynamics, or entropy-navigation events. Paper 0's
ENI-based diagnostics were therefore exercised only on
*hand-authored* fixtures where the upstream measurements were
**stipulated, not observed**.

### Assumption B — `focus_claim_id` is a label, not a tracked entity

Across all 30 hand-authored fixtures, the per-step focus is
functionally constant (`C001`). This is not a thinko; it is
consistent with treating the focus as a placeholder rather than a
tracked node in an evolving claim graph. The DESi `detect_terminal_attractor_subjects`
detector (pre-fix-1) treated focus-repetition as the primary
signal, which makes sense if focus is a label but not if it is
an evolving entity.

The empirical fact: real DES tracks focus_claim_id as the operand
of every operation, evolving from `C001` to `C009` across 35
operations. Focus IS an entity in real DES output. The pre-fix-1
attractor detector firing 20/20 on hand-authored fixtures
(generalization-loop baseline) was a direct consequence of this
mismatch.

### Assumption C — Recovery is measured at event boundaries

Paper 0 §8.1 and the cycle-7 composite classifier define recovery
as `dup_delta + novel_claims_next` at each EN event. This requires
EN events to be discrete pre/post snapshots — a quantum mechanic.

The empirical fact: real DES has continuous claim-graph evolution
with NO discrete pre/post snapshots. The closest entity-space
analog to "recovery" is "the created claim later becomes the
operand of further work" (cycle 4's `touch_count_after_creation`
classification). The cycle-4 metric is structural, not numerical.

### Assumption D — `birth(B) = (D, R, F, P, ΔQ)` is measurable in event-space

The 5-tuple from Paper 0 §12.1 (and the
`experiments/birth_criterion_falsification/` audit) measures
system-level properties of DESi. ΔQ in particular is measured as
"FP: 4 → 0; FN: 5 → 2" — both counted **on event-space fixtures**.

The empirical fact: when the same DESi rules are exercised on
entity-space input (real DES), they go silent (`step_coherence`
0/35, phases empty, EN classifications absent). Paper 0's ΔQ is
in-event-space-only. The external-reality challenge made this
explicit; this representation-gap report names the underlying
cause: ΔQ was never defined on a representation that real DES uses.

---

## 6. What Paper 1 must reconstruct explicitly

If a DESi-on-real-DES system is to satisfy a strengthened
birth criterion, Paper 1 must supply explicit reconstructions for
the assumptions Paper 0 left implicit:

### R1 — Define ENI in entity-space (or admit it doesn't transfer)

Paper 1 must answer: what numerical quantity, computable from
upstream DES output, plays the role of `eni_novelty`? Three
defensible options:

- **Lift the measurement to DES**. Add ENI computation to the DES
  scheduler. This makes DESi's existing event-space diagnostics
  applicable. Requires DES-side change.
- **Define an entity-space proxy**. E.g., "ENI at the loop where
  a new child claim is created = ratio of claim-attributes that
  differ from parent". Requires Paper 1 to commit to a specific
  formula and falsify it.
- **Acknowledge that event-space and entity-space diagnostics are
  separate stacks**. DESi-event-space continues to operate on
  synthetic; DESi-entity-space (`reconstruct_en_candidates` +
  `reconstruct_critique_navigation_candidates` + downstream-effect
  analyser) operates on real DES. The two are NOT merged.

### R2 — Define recovery in entity-space

Replace `dup_delta + novel_claims_next` with an entity-space
predicate. The cycle-4 `productive / dormant / terminal_anchor`
classification (touch_count + survival + terminal-focus) is a
candidate. Paper 1 should pick one and commit to it.

### R3 — Re-derive birth(B) components on entity-space

For each of the 5 birth(B) components (D, R, F, P, ΔQ), Paper 1
should state explicitly:
- What does this component MEAN on entity-space input?
- What does the measurement protocol look like?
- What evidence on real DES would force the component to 0?

The current Paper 0 §12.2 evaluation ("ΔQ > 0 because FP: 4→0;
FN: 5→2") cannot be ported wholesale because the FP/FN counters
themselves are event-space-defined.

### R4 — Acknowledge that "DESi diagnoses DES" is two systems

The honest description of the current state:

- **DESi-event-space**: ingests hand-authored EN-event-bearing
  trajectories; mature; pytest 58/58; rich rule set.
- **DESi-entity-space**: ingests upstream DES `operation_history`;
  immature; 4 detectors (parse_des_operation,
  reconstruct_en_candidates, reconstruct_critique_navigation_candidates,
  schema_mismatch); no phase / attractor / failure-mode diagnostics.

These are not two implementations of one system; they are two
systems with overlapping codebases that happen to share the name
"DESi". Paper 1 should either bridge them deliberately (R1) or
formally separate them (rename, distinct branches, distinct
release vehicles).

### R5 — Stop reporting in-distribution metrics as evidence of generalisation

Paper 0 §11.10 acknowledges "broader generalization ... remains
unestablished". Paper 1 should remove or qualify any sentence that
implies the event-space metric improvements (cycles 1-11 of the
self-improvement loop, cycles 1-7 of the generalization loop)
transfer to entity-space. They demonstrably do not (the external-
reality challenge measured `step_coherence` firing 34/35 on real
DES pre-fix; phases [] post-fix; zero ENI signal in any mode).
The metric improvements are improvements **on a representation**,
not improvements **of the system on its intended target**.

---

## Sources used (this report makes no new measurements)

- `experiments/external_reality_challenge/synthesis.md` —
  external-reality challenge headline.
- `experiments/external_reality_challenge/en_reconstruction/cycle_3/taxonomy_report.md` —
  35-operation taxonomy (3 EN, 3 critique-nav, 29 plain, 0
  unparsed, 0 unsupported).
- `experiments/external_reality_challenge/en_reconstruction/cycle_4/downstream_report.md` —
  5 productive + 1 terminal_anchor + 0 dormant.
- `experiments/external_reality_challenge/en_reconstruction/cycle_5/time_to_attention_report.md` —
  real-DES latency mean 15.17, hand-authored 0 candidates.
- `experiments/birth_criterion_falsification/synthesis.md` —
  D/R/F/P/ΔQ verdict.
- `experiments/semantic_drift_report.md` — the earlier mislabelling
  audit (`birth(B)` ≠ composite EN label).
- Paper 0 `DESi Paper-0 Birth v1-6.docx` §3 / §8 / §11 / §12.

No `src/desi/` source change. No new tests. No new detectors. No
new measurements. pytest 58/58 unchanged. The artefact is this
single markdown file.

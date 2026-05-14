# Paper 1 — Outline: The Representation Gap

**Working title**: *DESi II — From Event-Space Diagnostics to Entity-Space Reality*

**Source branch**: `experiment/desi-external-reality-challenge`.
This outline cites only artefacts already committed on that branch.
No new experiments are proposed inside this outline; each section
points at the file containing the corresponding evidence.

## Abstract (one paragraph, to be written from Section 10's synthesis)

Paper 0 established a lower-bound *birth criterion* for an epistemic
diagnostic system and reported `birth(B) = 1` for DESi under the
n=10 adversarial suite. Paper 1 reports what happened when the same
DESi was exposed to its first non-synthetic input: a real DES
trajectory dump (`hstre/DES` upstream). The system did not crash,
but its diagnostic output was dominated by an interface-failure
detector mislabelling missing data as contradictory data, and by
phase-detector false-positives caused by accidentally-satisfied
defaults. Three targeted interface fixes plus two phase-detector
guards eliminated the false-positive cascade. Two reconstruction
rules then extracted six structurally-verifiable navigation
candidates from native operation history; downstream-effect
analysis showed all six were consequential (5 productive, 1
terminal anchor, 0 dormant). A time-to-attention comparison
between synthetic and native trajectories proved formally
undefined, exposing the underlying issue: synthetic DESi fixtures
encode trajectories in **event-space** (discrete EN events with
numerical scores), while real DES emits trajectories in
**entity-space** (claims as named entities with operations on
them). Paper 0's birth criterion was implicitly event-space.
Paper 1 specifies the representation gap, the interface
discipline needed to bridge it, and the open work needed to
satisfy birth(B) under the strong (entity-space-aware) reading.

---

## 1. Paper 0 lower-bound birth

**Claim under review**: Paper 0 §12.1 defines
`B = (D, R, F, P, ΔQ)`, with `birth(B) = 1` iff all five
components are present. §12.2 reports
`D = 1, R = 1, F = 1, P = 1, ΔQ > 0` based on
`FP: 4 → 0; FN: 5 → 2` on the n=10 adversarial set, and concludes
`birth(B) = 1`. §12.3 explicitly frames this as a *lower bound*.

**Independent audit on this branch**:
`experiments/birth_criterion_falsification/synthesis.md`.

Per-component verdict (audit summary):
- D — weakly satisfied (pytest + suite metrics meet literal wording;
  architectural separation between detector and diagnosed system is
  not enforced).
- R — satisfied (revisions are concrete and measurable).
- F — satisfied in literal wording (revisions are testable;
  rejection tolerance documented).
- P — satisfied with two documented frictions (comment trimming
  + semantic-drift rename).
- ΔQ — satisfied **in-distribution only**; held-out unestablished.

**For Paper 1**: cite §12.3's lower-bound framing as load-bearing.
The five components are NOT independent; D, F, and ΔQ all share the
same hidden assumption that the test-input distribution is
representative of the deployment-input distribution. This sets up
Sections 2–8.

---

## 2. First external DES probe

**Source artefact**:
`experiments/external_reality_challenge/synthesis.md` plus
`experiments/external_reality_challenge/cycle_1/` (conservative
translation) and `cycle_2/` (heuristic translation).

**Setup**: real DES execution state (`hstre/DES` upstream
`des_state.json`) committed under
`experiments/external_reality_challenge/source/` with
`PROVENANCE.md`. 32 iterations, 9 claims, 35 operations. Authored
independent of DESi development. A translator
(`translator.py`) maps DES state schema to DESi trajectory schema
in two declared modes (conservative + heuristic).

**Headline finding (synthesis.md, F1–F7 + verdict table)**: DESi
did not crash. The dominant diagnostic output was
`step_coherence` firing on 34/35 steps with a misleading label,
plus three spurious phase fires. Under the strong reading of
components D and ΔQ from Paper 0 §12.1, this forces
`birth(B) = 0`. Under §12.1 as literally written (with §12.3's
lower-bound framing), the formal flag still reads 1 — but the
empirical evidence behind the §12.3 disclaimer is now in hand.

**For Paper 1**: this is the experiment that motivates the whole
paper. Section 11 of the manuscript (the audit) should present the
conservative-mode probe output verbatim from
`cycle_1/probe_output_PRE_FIX.json` and the heuristic-mode probe
output from `cycle_2/probe_output_PRE_FIX.json`.

---

## 3. Schema mismatch

**Source artefact**:
`experiments/external_reality_challenge/synthesis.md` §"Findings"
(F1–F7) and the underlying `cycle_1/evaluation.md` +
`cycle_2/evaluation.md`.

Three classes of mismatch, identified and named on this branch:

1. **Field-level mismatch.** Upstream DES emits no
   `novel_claims`, `dup_rate`, or `eni_*` fields. The DESi
   `cycle-6` `step_coherence` detector misclassifies these
   *absences* as *contradictions* (34/35 false positives in
   conservative mode).
2. **Operator-notation mismatch.** Real DES emits
   `T6[hypothesis_builder] on C003 -> C008` style strings; DESi's
   pre-fix regex only handled `Tn on Cxxx`. Six operations in the
   sample fell to a silent `UNKNOWN` substitution.
3. **Origin labelling absence.** No `input_origin` flag existed,
   so reports on translator-derived data were rendered with the
   same confidence as reports on hand-authored data.

**For Paper 1**: treat schema mismatch as the **diagnostic interface
problem** — distinct from any rule-level diagnostic problem. DESi
did not have a "trust the input?" detector. The empirical
consequence (Section 2 above) was that every downstream rule
inherited the input ambiguity.

---

## 4. Interface hardening

**Source artefacts**:
`experiments/external_reality_challenge/post_fix_deltas.md` and
`experiments/external_reality_challenge/post_phase_i_ii_fix_deltas.md`.

Five fixes total, applied to `src/desi/` while keeping all
hand-authored suites' diagnostic outcomes unchanged:

| # | Fix | Where |
|--:|---|---|
| 1 | `schema_mismatch` detection + `step_coherence` guard against missing-vs-contradictory | `models.py`, `diagnostics.py` |
| 2 | `parse_des_operation` handles richer notation + explicit `OPERATOR_PARSE_FAILURE` | `operator_parser.py` (new) |
| 3 | `input_origin` field + `render_report` disclaimer for non-native sources | `models.py`, `report_writer.py` |
| 4 | `detect_phase_i` silent when loop-0 metrics missing | `phase_detector.py` |
| 5 | `detect_phase_ii` silent when novel_claims missing across the pair | `phase_detector.py` |

**Headline metrics, pre → post** (post_fix_deltas + post_phase_i_ii):
- pytest: 35 → 49
- n=10 adversarial: every detector fire count unchanged
- n=20 generalization: every detector fire count unchanged
- external DES (conservative): `step_coherence` 34/35 → 0/35;
  spurious Phase I + II both gone; `phases = []`;
  `schema_mismatch = True (35/35 fields missing)`.

**For Paper 1**: present interface hardening as **necessary but
not sufficient**. The fixes make DESi *honest* on non-native input
(it no longer mislabels missing data as contradictory), but they
do not give DESi the ability to *diagnose* native DES. The
five-fix package raises the floor; the rest of the paper is
about whether a useful ceiling exists.

---

## 5. Reconstruction of structural navigation candidates

**Source artefacts** (`experiments/external_reality_challenge/en_reconstruction/`):
- `cycle_1/proposal.md`, `cycle_1/evaluation.md` — EN-candidate rule
- `cycle_2/proposal.md`, `cycle_2/evaluation.md` — critique-navigation
  rule (kept disjoint from EN by user directive)
- `cycle_3/taxonomy_report.md` — 5-way taxonomy of all 35 ops

Two reconstruction rules, each emitting candidates from native
operation history alone (no ENI fabrication):

```
EN candidate         iff sub_role == "hypothesis_builder" AND target ≠ None
critique-navigation  iff sub_role == "falsifier"          AND target ≠ None
```

Results on real DES (35 ops):

| Category | Count | Loops |
|---|---:|---|
| `reconstructed_EN_candidate` | 3 | 3, 7, 10 |
| `reconstructed_critique_navigation_candidate` | 3 | 4, 8, 11 |
| `plain_operator_transition` | 29 | rest |
| `unsupported_extension` | 0 | — |
| `unparsed_operation` | 0 | — |

Critical taxonomy measurements (cycle_3/evaluation.md):
- **Target-creating completeness = 6 / 6 = 100%**.
- Unparsed rate = 0%.
- Unsupported rate = 0%.

**For Paper 1**: emphasise that reconstruction does NOT recover
the ENI signal. It recovers **locations** — loop indices and
created-claim identities — where DES extended its graph via a
typed operation. The two categories are kept separate by design;
merging them would have erased the cycle-6 finding (Section 6
below) that the terminal anchor came from a critique, not a
construction.

---

## 6. Downstream validation

**Source artefact**:
`experiments/external_reality_challenge/en_reconstruction/cycle_4/`
(`proposal.md`, `downstream_effect.py`, `downstream_report.md`,
`evaluation.md`).

For each of the 6 reconstructed candidates (C004..C009), measured
from native DES fields only (no ENI fabrication):

- `first_focus_after_creation`
- `touch_count_after_creation`
- `survives_in_final_claims`
- `is_terminal_focus`

Classification (mutually exclusive, threshold = 3 touches):

| Class | Count |
|---|---:|
| `productive` | 5 |
| `terminal_anchor` | 1 (C009, the final focus) |
| `dormant` | 0 |

Four observations from cycle_4/evaluation.md:
- **O1.** Every reconstructed candidate is consequential. 0/6 dormant.
- **O2.** Creation-to-first-focus latency averages ~15 loops on real
  DES, vs. single-digit on hand-authored fixtures.
- **O3.** The terminal anchor (C009) came from a `falsifier`, not a
  `hypothesis_builder`. Critique-driven creation can be terminal.
  Defends the cycle-5 "do NOT merge into EN" directive (Section 5).
- **O4.** Pairing pattern: the 6 candidates form 3 hypothesis +
  falsifier pairs on the same parent claim (C002, C003, C003).

**For Paper 1**: cycle 4 supplies the first independent evidence
that the reconstruction rules pick up real productive nodes, not
noise. n = 1 trajectory; replication is open work (Section 10).

---

## 7. Time-to-attention undefined comparison

**Source artefact**:
`experiments/external_reality_challenge/en_reconstruction/cycle_5/`
(`proposal.md`, `time_to_attention.py`, `time_to_attention_report.md`,
`evaluation.md`).

Metric: `latency = first_focus_loop - creation_loop`. Computed
across three sources.

| Source | candidates | mean | median | variance |
|---|---:|---:|---:|---:|
| hand-authored n=10 adversarial | **0** | — | — | — |
| hand-authored n=20 generalization | **0** | — | — | — |
| native DES (n=1 trajectory) | **6** | **15.17** | **15.0** | **12.97** |

`LATENCY_DISTRIBUTION_MISMATCH` (per pre-defined rule
`real_DES_mean > 2 * synthetic_mean`): **UNDEFINED**. The synthetic
mean has no sample — division by an undefined denominator.

Two compounding reasons for the undefinedness (cycle_5/evaluation.md):
(a) the reconstruction rules require sub-role annotations that
hand-authored fixtures don't carry, and (b) hand-authored fixtures
keep `focus_claim_id` functionally constant, so even if (a) were
fixed, the first-focus signal would still be absent.

**For Paper 1**: the formal undefinedness is more informative than
a TRUE/FALSE answer would have been. It shows the *categorial*
gap — two corpora that ostensibly track the same phenomenon do
not even share a metric framework. This is the empirical entry
point for Section 8.

---

## 8. Event-space vs entity-space

**Source artefact**:
`experiments/external_reality_challenge/representation_gap_report.md`.

Frames the gap between synthetic and native input as a difference
in representation space, not a difference in dataset size or
trajectory shape.

**Event-space (synthetic DESi fixtures)**. Trajectory =
`(steps, en_events)`. The primary unit of analysis is the **EN
event**: a discrete moment with a numerical novelty score and
pre/post duplication snapshots. Per-claim identity is not
tracked (most fixtures use `focus_claim_id = "C001"` on every
step). ~8–10 distinct numerical signals per EN event.

**Entity-space (native DES)**. Trajectory =
`(claims, operation_history, focus_claim_id, iteration)`. The
primary unit of analysis is the **claim** (entity). Operations
are typed edges in a graph that creates, modifies, and references
specific named claims. No numerical novelty scores. ~7+ distinct
signals per graph-extending operation.

A mapping table in `representation_gap_report.md §1` shows the
two columns have no shared field. The latency-undefined result
(Section 7) is the direct consequence.

Four implicit Paper 0 assumptions that the gap exposes:
- A — Trajectories arrive in event-space.
- B — `focus_claim_id` is a label, not a tracked entity.
- C — Recovery is measured at event boundaries.
- D — `birth(B) = (D, R, F, P, ΔQ)` is measurable in event-space.

**For Paper 1**: present these four assumptions as the load-bearing
implicit content of Paper 0. The paper should state them
explicitly and then either *defend* them (and restrict DESi's
claimed scope to event-space) or *replace* them (and undertake the
work in Section 9).

---

## 9. Requirements for DESi entity-space

**Source artefact**:
`experiments/external_reality_challenge/representation_gap_report.md`
§6 ("What Paper 1 must reconstruct explicitly").

Five requirements, each cited verbatim from the source:

- **R1 — Define ENI in entity-space (or admit it doesn't transfer).**
  Three defensible options: lift ENI measurement to DES; define an
  entity-space proxy and falsify it; or formally separate
  DESi-event-space from DESi-entity-space.
- **R2 — Define recovery in entity-space.** Candidate operational
  predicate: cycle-4's `productive / dormant / terminal_anchor`
  classification.
- **R3 — Re-derive `birth(B)` components on entity-space.** For each
  of D, R, F, P, ΔQ, state the entity-space meaning, the measurement
  protocol, and what evidence on real DES would force the component
  to 0.
- **R4 — Acknowledge "DESi diagnoses DES" is two systems.**
  DESi-event-space (mature, hand-authored input, ~58 tests) and
  DESi-entity-space (~4 detectors, immature, ingests upstream DES).
- **R5 — Stop reporting in-distribution metrics as evidence of
  generalisation.** Paper 0 §11.10 already acknowledges this;
  Paper 1 should hold the line.

**For Paper 1**: these five form the methodological core of the
paper. Each requirement is presentable as a sub-section with
(i) statement, (ii) why Paper 0 didn't have it, (iii) candidate
formulation, (iv) what would falsify the candidate. The
representation_gap_report's text can be lifted with light editing.

---

## 10. Open work

Synthesised from the artefacts above; no new experiments
proposed inside this outline.

### O1 — Replication on additional DES dumps

Cycle 4's "5 productive + 1 terminal_anchor + 0 dormant" result
rests on **n = 1** real DES trajectory. The artefact
`cycle_4/evaluation.md` explicitly flags this as a limitation.
Replication on multiple independent DES runs would either
strengthen the productive-rate finding or surface the first
dormant candidate.

### O2 — Entity-space ENI formula

R1 from Section 9. Paper 1 cannot resolve this from existing
artefacts; the existing en_reconstruction cycles deliberately
emit *locations*, not *scores*. A formula choice + a falsification
suite would be a separate (post-Paper-1) experiment.

### O3 — Entity-space `birth(B)` re-derivation

R3 from Section 9. The audit in
`experiments/birth_criterion_falsification/` covers the
event-space reading of D/R/F/P/ΔQ. The entity-space reading is
unaddressed. Each of the five components needs an entity-space
measurement protocol and a falsification probe.

### O4 — Paired-builder/falsifier as a higher-order signal

Cycle 4's observation O4 (3 hypothesis + falsifier pairs on the
same parent) was noted but not implemented as a detector. A
cycle-3-style reconstruction rule could fire on the pair; this
was explicitly deferred ("one rule per cycle", cycle_2/proposal.md).

### O5 — Cross-validation of the hand-authored suites against
**entity-space-aware** fixtures

The hand-authored n=10 + n=20 suites do not exercise
`operator_sub_role` or `operator_target`. If a third suite of
hand-authored fixtures using the entity-space schema were
constructed, the existing DESi-entity-space detectors
(`reconstruct_en_candidates`, `reconstruct_critique_navigation_candidates`,
`schema_mismatch`) could be falsified independent of real DES.

### O6 — Falsifier reading-only paper section

The cycle-4 finding O3 (terminal anchor came from a `falsifier`)
is a small, citable result. It defends the cycle-5 disjointness
discipline empirically. Paper 1 could feature it as a section-long
case study rather than a one-line observation.

### O7 — Coverage replication on the upstream DES `des_prototype/`
state

`experiments/external_reality_challenge/source/des_prototype_state.json`
is also committed but no cycle ran the taxonomy on it. A
single additional run would either confirm the
`unparsed_rate = 0, unsupported_rate = 0, target-creating
completeness = 100%` results from cycle 3 or expose the first
counterexample.

---

## Appendix A — Artefact index

All cited artefacts live on
`experiment/desi-external-reality-challenge`:

| Section | Primary artefact(s) |
|--:|---|
| 1 | Paper 0 §12 (`DESi Paper-0 Birth v1-6.docx`), `experiments/birth_criterion_falsification/synthesis.md` |
| 2 | `experiments/external_reality_challenge/synthesis.md`; `cycle_1/` + `cycle_2/` |
| 3 | `experiments/external_reality_challenge/synthesis.md` (F1–F7) |
| 4 | `post_fix_deltas.md`; `post_phase_i_ii_fix_deltas.md` |
| 5 | `en_reconstruction/cycle_1/`; `cycle_2/`; `cycle_3/` |
| 6 | `en_reconstruction/cycle_4/` |
| 7 | `en_reconstruction/cycle_5/` |
| 8 | `representation_gap_report.md` |
| 9 | `representation_gap_report.md` §6 |
| 10 | derived; see per-item citations |

## Appendix B — Constraints honoured by this outline

- **No DESi source change.** This file is `docs/paper1/`, not
  `src/desi/`. pytest 58/58 unchanged at the time of writing.
- **No new experiments proposed inside the outline.** Section 10
  identifies open work but defers actual execution to future
  cycles outside Paper 1's scope.
- **Only existing artefacts cited.** Every reference resolves to a
  file already on `experiment/desi-external-reality-challenge`
  at HEAD `50e6a19` or earlier.

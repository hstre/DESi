# Gate-Governed Architecture: DESi v3 Methodology

**Version:** v3.24 paper draft (frozen consolidation of v3.4 – v3.23).
**Status:** Methodology paper. No new architecture; pure synthesis of
twenty completed audit and patch cycles. Every quantitative claim in
this paper is machine-verified against the corresponding
`artifacts/v3_*/report.json` file via `docs/papers/v3_claims.json`.

---

## 1. Problem

DESi (Dynamic Epistemic Self-inspection) is a research prototype for
**auditable epistemic AI**. The v1 line built a logical-audit layer
that decided whether a claim was `LOGICALLY_SUPPORTED` based on a
closed set of inference rules. The v2 line extended this to multi-step
chains and surfaced a recurring failure mode: the same chain text
could be classified differently depending on which *frame* (physical,
logical, metaphorical, …) the reader assumed. v3 began with this
observation.

The central problem v3 addresses: **how does a reasoning system
prevent the surrounding context — section headers, document frames,
authority cues — from silently substituting for the reasoning the
sentence itself supports?** The answer the v3 line arrives at is
**gate governance**: a pipeline of seven discrete refusal points,
each with an independent predicate, in series. The architecture is
not "compute a better explanation" — it is "know exactly where to
refuse passage."

---

## 2. Prior Failure Modes

Three failure modes drove the v3 line, each documented in a v3.x
audit that quantified the problem before any patch:

* **Frame polysemy (v3.4 – v3.7).** A claim like *"entropy increases"*
  is thermodynamically true and information-theoretically false. The
  v3.4 frame benchmark surfaced 40 cases that needed a frame
  declaration to be unambiguous. v3.5's invariance probe and v3.6's
  failure-cluster audit catalogued the 30 cases where polysemy
  produced incorrect verdicts. v3.7's disambiguator probe explored
  per-frame marker tokens and concluded the symbolic patch space
  was insufficient.
* **Inheritance absorption (v3.8 – v3.10).** When an outer frame is
  attached to a claim (via a section header or explicit `Frame:`
  marker), naïve inheritance lets the outer overwrite the inner.
  v3.8's context-inheritance probe measured a 100 % absorption rate
  on 10 false-inheritance fixtures: the outer always won.
* **Adversarial bypass (v3.15).** Once tension detection (v3.9) and
  routing (v3.13) were in place, a red-team probe constructed 100
  adversarial chains designed to bypass the v2.7 `CAUSAL_CHAIN`
  guards. 93 of 100 succeeded. v3.15 made the bypass surface
  meaß­bar.

Each failure mode is a separately replayable artifact. None has been
silently revised.

---

## 3. Frame Declaration

v3.4 introduces `FrameDeclaration`: a closed-enum tag attached to
every claim during pipeline entry. Frame kinds are
`THERMODYNAMIC`, `INFORMATION_THEORETIC`,
`ONTOLOGICAL_DISTINGUISHABILITY`, `METAPHORICAL`, `FORMAL_LOGIC`,
`EMPIRICAL_CAUSAL`, `AUTHORITY_SPEECH`, `TOOL_COMPUTABLE`, and
`FRAME_UNDECLARED`. The v3.4 detector reaches 40 / 40 on a 40-case
benchmark (claim **C-v34** in `v3_claims.json`).

The detector's promise is bounded: it provides a *tag*, not a
*verdict*. Downstream gates consult the tag to decide whether to
route a claim into a frame-specific pipeline. The detector itself
never accepts or rejects.

---

## 4. Frame Tension

v3.9 introduces `FrameConsistency`: a closed four-value verdict over
the inner frame (extracted from the claim text alone) and the outer
frame (extracted from inherited context alone).

```
inner == outer (single declared frame)  →  CONFIRMED
inner ≠ outer, pair conflict-capable     →  TENSION
inner ≠ outer, hard contradiction        →  CONFLICT
inner or outer missing / multi-bucket    →  UNDECIDABLE
```

The classifier is run **twice** on every claim: once by the
v3.11 runtime `FrameTensionLayer` (Aufgabe 7 of v3.11) and once
again by the v3.13 router as a routing prerequisite. The two
invocations are independent; the same `FrameDetector` is used,
which guarantees determinism but not independence.

v3.11's runtime benchmark of 40 cases reaches 40 / 40 accuracy
(claims **C003–C005**). The adversarial probe of 20 v3.9
manipulation cases produces `manipulation_detection_rate = 1.000`
and `false_inheritance_allowed = 0` (claims **C001 / C002**).

---

## 5. Routing Authority

v3.13 attaches a hardcoded routing decision to every consistency
verdict:

```
CONFIRMED   → route to inferred pipeline           (FRAME_ROUTING_ALLOWED)
TENSION     → block inheritance, route via inner    (FRAME_ROUTING_INNER_ONLY)
CONFLICT    → reject                                (FRAME_ROUTING_BLOCKED)
UNDECIDABLE → refuse until explicit marker          (FRAME_ROUTING_MARKER_REQUIRED)
```

The pipeline targets are `tool_gate`, `logical_auditor`,
`consilium`, `reject`. The mapping is *not* configurable: it is
the only routing policy v3 admits.

v3.13's 70-case integration benchmark (30 manipulative + 20
normal + 20 ambiguous) reaches 70 / 70 (claims **C010–C012**). The
adversarial test on the v3.9 manipulation set produces
`inherited_manipulations = 0` and `routed_manipulations = 0`
(claims **C015 / C016**). Two complete pipeline runs produce
identical state hashes (claim **C019**).

---

## 6. CAUSAL_CHAIN

v2.7's `InferenceRule.CAUSAL_CHAIN` is the only rule in the v1.2
inference set that handles multi-premise sequential reasoning. v3.14
validates it on a 60-case held-out benchmark constructed from
domains intentionally disjoint from v2.3's discovery corpus
(pottery, music, beekeeping, sailing, astronomy, origami, etc.).

The held-out result is `heldout_precision = 1.000`,
`heldout_recall = 1.000`, `false_positive_count = 0`,
`trap_block_rate = 1.000` (claims **C020 – C024**). Independence is
verified against v2.3 and v2.6: `exact_text_overlap = 0`,
`lexical_overlap_mean = 0.058` (claims **C030** / paper text).

v3.14 thereby establishes that the v2.7 rule + its eight guards
generalise outside the discovery set across the five known trap
families (linear-causal, conditional, contradiction, cycle,
false-causal).

---

## 7. Suspension Gates

v3.16 patches `_try_causal_chain` with six v3.16 marker extensions:

```
_V316_NEGATION_EXTENSIONS         (synonym bypass for "not"/"never")
_V316_QUANTIFIER_EXTENSIONS       (synonyms for "all"/"every"/"some")
_V316_AUTHORITY_LIKE_VERBS        (verbs beyond v1.8's lemma set)
_V316_METAPHOR_MARKERS            (X-is-Y identification phrases)
_V316_CYCLE_REF_EXTENSIONS        (synonyms for "depends on")
_V316_NUMBER_WORDS                (tool-contamination detection)
```

Any v3.16 guard triggering returns `None` from the rule. The
existing `LogicalAuditor` pipeline then routes the chain via
`_classify_gap` into an existing `LogicalState`
(`LOGICALLY_REJECTED`, `BRIDGE_REQUIRED`, or `GAP_DETECTED`).
**No new ClaimStates were introduced.** The suspension is
expressed entirely through existing pipeline behaviour.

v3.16's outcome: the v3.15 adversarial corpus drops from 93 / 100
attack successes to 24 / 100 (claim **C044**). v2.7 reconstruction
and fail-case hashes both stay bit-identical
(`1f4d9dfe44cb16e1` and `d83d81ab8417c022`) — the rule's
declarative metadata is unchanged. v3.14 recall stays at 1.000
(claim **C048**); v1.5 precision stays at 1.000 (claim **C049**);
v3.13 manipulation detection stays at 1.000 (claim **C050**).

---

## 8. Adversarial Findings

v3.15 — Causal Chain Adversarial Construction. 100 chains across
eight attack families:

| Family | Successes |
| --- | ---: |
| A_hidden_negation | 14 / 15 |
| B_quantifier_drift | 15 / 15 (claim **C038**) |
| C_authority_insertion | 12 / 15 |
| D_metaphor_insertion | 14 / 15 |
| E_frame_switch | 15 / 15 (claim **C036**) |
| F_tool_contamination | 8 / 10 |
| G_cycle_disguise | 10 / 10 |
| H_semantic_leap | 5 / 5 (claim **C037**) |

Total 93 / 100 = 0.93 (claim **C031**).

The v3.15 cross-frame probe runs the same attacks through both the
v3.13 router and the v2.7 chain (claims **C039 – C041**):

* `chain_only_attacks = 93` (chain layer alone supports them)
* `routing_prevented_attacks = 81` (router catches 81 of the 93)
* `combined_false_support = 12` (both layers let through)

The pipeline as a *composition* shrinks the attack surface from
93 % to 12 %. No single layer eliminates it.

---

## 9. Gate Ablation

v3.21 masks each of the seven gates in turn and measures the
per-gate effect on seven defensive metrics (attack_success_rate,
heldout_recall, false_positive_count, contamination_count,
trajectory_separability, routing_integrity,
manipulation_absorption).

Classification: `DEAD_KNOB` if `max_delta < 0.05`,
`PRIMARY_CLIFF` if `max_delta > 0.50`, `SUPPORT_LAYER` between.

Six gates classify as `PRIMARY_CLIFF`
(`PremiseExtractor`, `SPL`, `FrameTension`, `FrameTensionRouter`,
`CAUSAL_CHAIN`, `SuspensionGate`); one classifies as `DEAD_KNOB`
(`FrameDeclaration`). Claims **C089 / C090**.

The `FrameDeclaration` dead-knob result is context-dependent: in
the v3.21 corpus the inherited context is empty, so masking
`FrameDeclaration` does not propagate any visible change.
Under non-empty production context the gate would re-enter
play.

v3.21 contamination is zero (claim **C088**); the audit's own
machinery is therefore valid even when the production corpus
exposes the v3.16-surviving residual.

---

## 10. Gate Ordering

v3.22 simulates eight gate orderings (current order plus seven
permutations) and tests whether any ordering improves
`attack_success_rate` without violating the safety floor on
recall, false_routes, contamination, and valid_block_rate.

All eight orderings produce the **same** `attack_success_rate = 0.195`
(claim **C095**). The order shifts *when* a gate fires, not
*which* chains slip through. The v3.16-surviving residual is a
per-chain phenomenon of `SuspensionGate`'s predicate, not of any
ordering choice. `best_ordering = null` (claim **C096**);
`recommended_next = KEEP_CURRENT_ORDER` (claim **C097**).

---

## 11. Latency Orthogonality

v3.23 evaluates three stacks (S1 current_order, S2
maximal_safe_stack, S3 minimal_without_causal_chain) and
measures both safety metrics and latency cost.

`S1 baseline latency_cost = 10.44` (claim **C102**). S2's
`maximal_safe_stack` reaches `latency_cost = 6.46` — a **38 %
latency reduction** — with **identical attack_success_rate**,
**identical heldout_recall**, and a 73 % drop in
`false_route_count`. The improvement comes from moving
`SuspensionGate` from gate position 7 to position 3, letting
adversarial chains terminate before the routing and audit
layers run.

The directive's `contamination = 0` hard gate falls on the
corpus-inherent 85 v3.16-surviving cases (claim **C103**), so the
report's `recommended_next = NONE` (claim **C105**). The
empirical finding nonetheless stands: latency optimisation is
orthogonal to security in this architecture. A future audit
running on a corpus that excludes the v3.16-surviving residual
would surface S2 as `LATENCY_OPTIMIZED_STACK`.

---

## 12. Limitations

1. **Geometric separability is genuinely low.** v3.18, v3.19, and
   v3.20 all measured the valid-vs-adversarial separability in
   different feature spaces. None reached 0.80. Adversarial corpora
   are constructed to sit close to valid corpora in any lexical
   geometry. The pipeline's protection is not geometric — it is
   structural (gate decisions).
2. **The v3.16-surviving residual persists.** 24 of 100 v3.15
   attacks remain `LOGICALLY_SUPPORTED` after the v3.16 patch
   (claim **C044**). 15 are frame-switch chains and 5 are pure
   semantic non-sequiturs — both classes are structurally
   indistinguishable from valid sparse chains via marker
   detection.
3. **`paraphrase_instability` (v3.20) is brittle.** The signal
   is computed against a punctuation perturbation that breaks the
   v1.2 chain-detection heuristic for most chains. It appears in
   the feature vector but is excluded from the binary NC anomaly
   flag — a documented compromise.
4. **`FrameDeclaration` classification depends on corpus.** v3.21
   marks it `DEAD_KNOB`. The label is honest for the empty-context
   test corpus but does not generalise to production traffic with
   inherited context.
5. **NC accuracy < 1.0 in v3.18 and v3.20.** v3.18 reaches 0.96 on
   54 NCs; v3.20 reaches 0.96 on 50 NCs. The weird-marker-free
   shape in v3.18 is correctly classified 0 / 13 of the time — a
   structural blind spot of marker-based detection that no
   relabelling fixes.

---

## 13. Falsified Hypotheses

The v3 line followed a sequence of audits, each formulated as a
testable hypothesis. Ten hypotheses were falsified by subsequent
data:

1. **"Token-pair disambiguation can resolve frame polysemy" (v3.7).**
   The Occam-optimal candidate `entropy + one` is semantically
   hollow; coverage caps at 0.467; no candidate clears all four
   gates with semantic basis. → v3.7 `recommended_next = NONE`.
2. **"Local context inheritance fixes the polysemy problem" (v3.8).**
   The naïve simulator absorbs 10 of 10 misleading-window
   fixtures and 34 of 57 fixture phrases overlap protected pools.
   → v3.8 `recommended_next = NONE`.
3. **"v2.7 CAUSAL_CHAIN is robust against unknown attacks" (v3.14
   → v3.15).** v3.14's positive generalisation result was
   bounded by the v2.6 trap taxonomy. v3.15's red-team probe
   showed 93 / 100 attacks succeed against precisely the same
   rule. → v3.15 falsifies v3.14's robustness reading; both
   reports stand.
4. **"Marker-naturalness can flag adversarials" (v3.18).** Over-
   explained chains are correctly flagged (13 / 13), but
   marker-free non-sequiturs go undetected (0 / 13). False alarm
   rate 0.20 violates the 0.05 threshold. → v3.18
   `recommended_next = NONE`.
5. **"Trajectory geometry separates valid from adversarial" (v3.19).**
   Separability in the 9-dim closed feature space is 0.28 —
   below the 0.80 threshold. → v3.19 `recommended_next =
   CAUSAL_CHAIN_DEPRECATION_PROBE`, which itself becomes v3.20.
6. **"CAUSAL_CHAIN is a dead knob and can be deprecated" (v3.19
   → v3.21).** v3.19 marks it dead in the trajectory
   geometry; v3.21 marks it `PRIMARY_CLIFF` in the structural
   ablation (Δ heldout_recall = 0.65). Both are reproducible in
   their own register; the v3.19 reading is falsified by v3.21's
   ablation result.
7. **"PremiseExtractor is the primary defender" (v3.20).** The
   hypothesis was extracted from v3.19's data. v3.20's per-signal
   masking probe falsified it directly: all 11 signals classify as
   `DEAD_KNOB`; baseline separability is 0.048. → v3.20
   `recommended_next = NONE`.
8. **"Type-restricted CAUSAL_CHAIN (only physical / institutional
   / logical link types) keeps protection while shrinking
   surface" (v3.17).** The restriction would cull 90 % of v2.3
   and 68 % of v3.14, and 25 v3.15 attacks still slip through.
   → v3.17 `recommended_next = NONE`.
9. **"Reordering gates improves security" (v3.22).** Every
   tested ordering produces the same `attack_success_rate = 0.195`.
   Reorder moves *latency*, not effectiveness. → v3.22
   `recommended_next = KEEP_CURRENT_ORDER`.
10. **"Removing CAUSAL_CHAIN improves recall" (v3.23 S3).** S3
    reaches `heldout_recall = 0.893` (vs 0.649 baseline), but
    every additional pass-through chain lacks a
    `LOGICALLY_SUPPORTED` verdict. The recall gain is
    verdict-avoidance, not verdict-improvement. → v3.23 reports
    S3 as `SIGNIFICANT_GAIN` on latency only; safety reading is
    neutral.

Each falsification is anchored to the relevant artifact in
`v3_claims.json`. The pattern is intentional: the architecture
that emerges is the one that survived every audit.

---

## 14. Deployment Criteria

The v3 line produces three runtime patches (v3.11, v3.13, v3.16)
and twenty read-only audits. A deployment-quality verdict requires
every prior hash to remain bit-identical and every audit gate to
clear. The criteria observed across v3.11 → v3.23:

* `v2.8 reconstruction replay_hash` = `1f4d9dfe44cb16e1` (pinned in
  v3.11, v3.13, v3.14, v3.16, v3.21, v3.22, v3.23 regression
  suites).
* `v2.8 fail-case replay_hash` = `d83d81ab8417c022` (same).
* `v3.4 frame_benchmark` produces `40/40 fully_correct` (pinned
  across every v3.X regression suite).
* `v3.5 invariance` produces `400 cases` (pinned).
* Every v3.X artifact's `replay_hash` is pinned in the next
  audit's regression test set.
* `nc_accuracy >= 0.95` is enforced as a hard gate in every audit
  that includes NCs (v3.7, v3.8, v3.9, v3.10, v3.11, v3.13,
  v3.14, v3.15, v3.16, v3.17, v3.18, v3.19, v3.20, v3.21,
  v3.22, v3.23).

A future audit that fails any of these is automatically blocked
by the regression suite; the v3.24 paper itself depends on
`v3_claims.json` matching the artifacts exactly.

---

## 15. Conclusion

DESi's v3 line produces a defence architecture composed of seven
discrete gates, six of which (v3.21 ablation result) each carry
independent defensive load. The architecture is not built around a
single clever inference rule. It is built around *knowing exactly
where to refuse passage*.

Three runtime patches (v3.11 routing-aware tension layer, v3.13
hardcoded router, v3.16 marker-based suspension) sit on top of
the v1.2 logical-audit base and the v2.7 chain rule. Seventeen
read-only audits surround those patches with continuous data
about what works, what doesn't, what falsifies what.

The honest summary of the v3 line:

* **v3.4 — v3.13** build the gate stack incrementally, each patch
  validated against the prior bit-identical hash set.
* **v3.14** confirms structural robustness of CAUSAL_CHAIN against
  five known trap families.
* **v3.15** finds the trap families that v3.14 did not cover —
  93 / 100 attack success.
* **v3.16** patches the bypass surface — 93 → 24, while preserving
  every prior hash.
* **v3.17 — v3.20** test four hypotheses about *why* the defence
  works (link types, naturalness, trajectories, extractor signals).
  Each is honestly falsified.
* **v3.21** measures the actual gate stack: six PRIMARY_CLIFFs.
* **v3.22** measures ordering effects: no security gain, but a
  latency hint.
* **v3.23** confirms the latency hint: 38 % reduction available
  at zero security cost, blocked from deployment only by the
  corpus-inherent v3.16-surviving residual.

The v3 line ships a tested, falsifiable, bit-reproducible
architecture. v3.24 freezes it for citation.

---

## Appendix: Drift, contradiction, replay tests

`tests/paper_v3/` contains three test suites:

* `test_drift.py` — loads `v3_claims.json`, verifies every claim's
  `expected_value` matches the live artifact at `field_path`. Drift
  count must be 0.
* `test_contradictions.py` — pairwise check that no two claims
  reference the same `(artifact, field_path)` with different
  expected values.
* `test_reproducibility.py` — two independent loads of
  `v3_claims.json` must produce identical content hashes; same for
  the paper Markdown file.

Two complete generations of `v3_claims.json` produce identical
content hashes (claim infrastructure invariant). The paper itself
is plain Markdown — its content hash is a function of its bytes.

---

## Reflection

> *"When does an architecture stop being a collection of patches
> and become a scientific position?"*

A position emerges when each patch (a) is verifiable against
data its author did not see, (b) survives later audits whose
hypotheses contradict its assumptions, and (c) sits in a
reproducible test suite that catches drift. v3.14 saw v3.11.
v3.15 falsified v3.14's optimism. v3.16 patched on top of v3.15.
v3.19's optimism about trajectory geometry was falsified by
v3.20's extractor-signal probe. v3.20's optimism about
extractor primacy was falsified by v3.21's gate ablation. v3.21
identified six cliffs; v3.22 confirmed they cannot be reordered
for security; v3.23 confirmed they can be reordered for latency
at zero security cost.

Twenty independently-reproducible audits stand. Three runtime
patches stand. Ten hypotheses fell. The bit-identical hash set is
intact across all twenty-four releases. This is the v3 position
DESi commits to.

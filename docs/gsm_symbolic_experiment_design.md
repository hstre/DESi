# GSM-Symbolic as a DESi Frame-Invariance Probe — Experiment Design

> **Headline (deliberately dry):** DESi tests whether explicit
> *content/method separation* reduces **template-level behavioral variance
> under symbolic perturbation** — not whether DESi improves mathematical
> reasoning.
>
> **Status:** planning only. No connector, runner, dataset or live-LLM run
> exists yet. This document fixes the framing, the metrics, and the
> honesty/determinism boundaries *before* any code is written, so that a
> later implementation sprint cannot quietly drift into an
> "LLM solves math better" accuracy claim.
>
> **External anchor:** Mirzadeh, Alizadeh, Shahrokhi, Tuzel, Bengio,
> Farajtabar (Apple), *"GSM-Symbolic: Understanding the Limitations of
> Mathematical Reasoning in Large Language Models"*; data and templates at
> `github.com/apple/ml-gsm-symbolic` and `huggingface.co/datasets/apple/GSM-Symbolic`
> (families GSM-Symbolic, GSM-Symbolic-P1, GSM-Symbolic-P2). Treated as an
> **unverified external claim** — this experiment does **not** endorse the
> paper's "LLMs do not reason" interpretation, and is compatible with the
> later re-evaluations that attribute part of the effect to number-range
> distribution shift.

---

## 1. What DESi can and cannot claim here

DESi is a deterministic, read-only, non-authoritative epistemic
structuring/governance layer (no PRNG, no learned model, replay-stable,
`sha256` signatures). It is **not a solver** and does not compete on
accuracy leaderboards. That constraint *shapes* this experiment rather than
blocking it.

- **Not claimed:** "DESi makes the model better at arithmetic."
- **Not claimed:** "GSM-Symbolic proves LLMs cannot reason."
- **Claimed (falsifiable):** *Structuring a GSM-Symbolic item into an
  explicit DESi state — separating surface form, irrelevant clauses, and
  the operation chain — reduces the **variance of outcomes across
  instantiations of the same template**, measured by a group-invariance
  rate, relative to handing the raw text to the same model.* The headline
  is **epistemic stabilisation, not compute.**

**What a negative result means (read before celebrating any score):**

- If invariance does **not** improve (or the NoOp gap does not shrink),
  that is a clean negative result and must be reported as such.
- **If DESi improves accuracy but not invariance, the result does *not*
  support the DESi thesis.** Higher scores with flat
  `group_invariance_rate` are an accuracy artifact, not stabilisation, and
  must not be reframed as a win. This guard exists specifically to stop a
  late slide back into accuracy marketing.

---

## 2. Why GSM-Symbolic fits DESi

GSM-Symbolic is, at its core, an **invariance test**: many instances are
generated from one symbolic template by swapping names/numbers (P1) and by
adding clauses, including reasoning-irrelevant "NoOp" clauses (P2). A model
that genuinely captured the problem *structure* would answer every instance
of a template consistently. That is precisely the question DESi's
`frame_invariance` subsystem already asks about paraphrase groups.

The mapping is almost 1:1:

| GSM-Symbolic concept | DESi analogue (already in `src/desi`) |
|---|---|
| One template, many instances | `frame_invariance` **ParaphraseGroup** (a group of variants expected to behave identically) |
| "Do all variants stay consistent?" | `frame_invariance.metrics.group_invariance_rate` |
| Name/number swap (P1) | `t10_vocabulary`, `t10_rename`, `t10_semantic`, `t10_structural_vocab` (surface-variation invariance) |
| Irrelevant / NoOp clause (P2) | `content_method`, `content_only_resonance`, `method_only_resonance` (content vs. method separation) |
| Ingesting an external dataset | `external_benchmarks` connector (`NormalizedTask`, hashed + provenance-bound) |
| Running a real model for A/B | `live_llm_validation` (+ `live_llm_validation_deepseek`) |

There is also strong **precedent**: DESi already runs external
baseline-vs-DESi A/B studies on other suites (branches
`gaia-desi-adapter`, `truthfulqa-solo-vs-desi`, the `desi-ab-*` family,
`static-benchmark-suite`, `experiment/desi-external-reality-challenge`).
GSM-Symbolic slots into that established pattern.

**Explicit non-hook:** `open_math/` is a "wild exploration sandbox" for
hypothesis governance (`no breakthrough claims`), *not* arithmetic word
problems. Do **not** wire GSM-Symbolic there.

---

## 3. Existing machinery to reuse (and what must be new)

**Reuse the metric *shape*, not the runner verbatim.**
`frame_invariance/metrics.py` defines `FrameInvarianceMetrics` with
`group_invariance_rate`, `per_frame_invariance`, `frame_accuracy`,
`conflict_rate`, plus `weakest_frame` / `strongest_frame` and a
`failure_distribution`. The *definition* of group invariance (a group is
invariant iff every member is mutually consistent) is exactly what we want.

But `FrameInvarianceRunner` currently decides a **FrameKind per case** over
`frames` / `ClaimState`; it does not check arithmetic-answer equality. So a
GSM-Symbolic run needs:

- a **GSM adapter** that turns answer-equality-within-template into the
  same group-invariance shape (group = template_id; member-correct =
  final answer matches the instance's gold answer), and
- the layered invariance + NoOp + cost metrics of §5, which have no
  existing analogue and must be added.

**Reuse directly:**

- `external_benchmarks.task_normalizer.NormalizedTask` + `replay_key()`
  (`sha256`) and `dataset_hashing` for provenance-bound, versioned
  ingestion. **Preserve `template_id` and `instance_id` in the payload**
  so groups can be reconstructed deterministically.
- `external_benchmarks.benchmark_registry` to register a new family
  (`gsm_symbolic`, with P1/P2 as sub-families or routes).
- `external_benchmarks.report` verdict vocabulary
  (`VERDICT_INGESTED` / `VERDICT_PARTIAL` / `VERDICT_HALT`) for the
  connector stage.
- `live_llm_validation*` for the actual model calls in the A/B stage.

---

## 4. Experiment architecture

```
                 apple/ml-gsm-symbolic (vendored, hashed, offline)
                              |
                  external_benchmarks connector
              (NormalizedTask: + template_id, + instance_id,
               dataset_version, content_hash, provenance)
                              |
             +----------------+----------------+
             |                                 |
        BASELINE arm                       DESi arm
     raw item text -> LLM            item -> DESi state (Level A/B,
                                      Level C ablation-only) -> LLM
             |                                 |
             +----------------+----------------+
                              |
             group by template_id; per arm compute:
             - strict group correctness  (headline)
             - answer consistency / error-stability (diagnostic)
             - NoOp gap (P2 drop from irrelevant clauses)
             - compute cost (tokens, latency)
                              |
                report (markdown + JSON artifact)
          baseline vs DESi; deltas; negative controls
```

### 4.1 The DESi state must not smuggle in the solution

The single biggest validity risk is that the DESi structuring pass quietly
*solves* the problem, so the comparison becomes "a model that solved it once
in the state vs a model that solved it once in the prompt." To prevent that,
the DESi state is **stratified**, and the headline run uses only Levels A+B:

- **Level A — representation only:** entities, quantities, units, candidate
  relations, **suspected** irrelevant clauses. No operations.
- **Level B — operation *constraints*:** which quantities may combine, types,
  expected answer type — **but no arithmetic execution and no ordered
  solution steps.**
- **Level C — full operation chain:** the ordered solution plan. **Ablation
  only**, reported separately, never in the headline number.

This lets the result distinguish *"pure relevance/structure separation
already stabilises behaviour"* (A+B) from *"stabilisation only appears once
you hand the model a near-complete plan"* (C). Only the former supports the
DESi thesis cleanly.

---

## 5. Metrics — invariance first, accuracy second

### 5.1 Primary: layered invariance (the thesis stands or falls here)

A single "all variants correct" rate hides too much (9/10 correct collapses
to the same 0 as 1/10). Report three layers; the **strict** one is the
headline, the softer two are diagnostic:

- **Strict Group Correctness (HEADLINE):** share of templates for which
  **all** sampled instances are correct. This is the rigorous
  `group_invariance_rate` from `frame_invariance`.
- **Answer Consistency (diagnostic):** share of templates whose variants
  produce the **same structural answer status** — even when they are jointly
  *wrong*. Measures behavioural stability independent of correctness.
- **Error-Stability (diagnostic):** among failing templates, whether errors
  are *of the same kind* across variants rather than randomly drifting.
  Stable-but-wrong is a different (and more DESi-relevant) signal than
  chaotic failure.

- **Template Stability Gain** = `StrictGroupCorrectness(DESi)` −
  `StrictGroupCorrectness(baseline)`. The single number that matters.

### 5.2 NoOp gap (the publishable core)

- **NoOp gap** = (accuracy on base instance) − (accuracy on the same
  instance with a reasoning-irrelevant clause added), per arm. Thesis
  prediction: DESi's NoOp gap < baseline's, because the irrelevant clause
  is flagged at Level A and excluded from the Level B constraints. This is
  the most DESi-native, most publishable axis (a structural claim, not a
  score claim).

### 5.3 Compute cost (guards against "more steps, of course it's better")

Reported as a first-class block, **not** as the thesis, to keep the
comparison honest (structured pipeline vs raw prompting):

- `tokens_baseline`
- `tokens_desi_state_generation` (Level A/B; Level C separately)
- `tokens_desi_solver_call`
- `latency_total` (both arms)
- `cost_per_correct_invariant_template` — normalises stability gain by spend

### 5.4 Secondary / diagnostic

- `frame_accuracy` per arm (report it, but it is **not** the headline).
- Number-swap variance (P1): variance of correctness across instances of a
  template under pure value substitution.
- Per-template `weakest_frame` / `strongest_frame`-style ranking to surface
  *which* templates DESi stabilises and which it does not.

### 5.5 Negative controls (mandatory) — three clause types

Mirror and extend `frame_invariance.NEGATIVE_CONTROLS`. The third type is
the decisive one: it checks whether DESi separates *meaning* or merely
filters on "sounds like a side note."

1. **NoOp clause:** irrelevant; **must be ignored** (excluded from Level B).
2. **Load-bearing clause:** relevant; **must not be ignored**. If DESi drops
   it, content/method separation is overreaching → result invalid.
3. **Adversarially-similar clause:** phrased like a NoOp (incidental,
   parenthetical, "by the way…") but **computationally relevant**. Tests
   whether DESi tracks semantics or just surface cues. A system that fails
   only here is pattern-matching, not separating meaning.

---

## 6. Honesty & determinism boundaries (the real constraints)

Two invariants of the DESi core must survive contact with real data and a
real model:

1. **Real data enters only via the connector.** `external_benchmarks`
   already states its honesty rule: *locally-vendored reference sets in the
   published format — not live downloads, not official leaderboard scores.*
   GSM-Symbolic data is vendored under
   `src/desi/external_benchmarks/datasets/`, content-hashed and
   provenance-tagged. It is **never** inlined into a synthetic sandbox
   fixture and never presented as a "DESi result." Apple's license and
   attribution travel with the vendored copy.
2. **Live-LLM output is not replay-stable** → it must be quarantined from
   the deterministic core: outside the determinism scanner / replay-hash /
   full-regression invariants, exactly as `live_llm_validation` is today.
   All A/B numbers are labelled **real, single-run, model+date-stamped**,
   not deterministic sandbox values. The connector and metric *definitions*
   stay deterministic and testable with a stub model.

Forbidden-term governance still applies to any rendered report (no "AGI",
"world model", "breakthrough", "reasoning engine", etc.).

---

## 7. Phased plan (mirrors DESi sprint style)

| Phase | Deliverable | Determinism | Gate |
|---|---|---|---|
| **G0 Connector** | `gsm_symbolic` family in `external_benchmarks`; vendored sample slice (a few templates × N instances for GSM-Symbolic + P1 + P2); `NormalizedTask`s preserving `template_id`/`instance_id`; hashing + provenance tests | deterministic | dataset hash visible, normalization integrity = 1.0 |
| **G1 Grouping + metrics** | GSM adapter; layered invariance (§5.1), NoOp gap, cost block, three-type negative controls; all on a **stub model** so it is replay-stable | deterministic | metrics reproduce byte-stable on replay |
| **G2 Baseline vs DESi (live)** | DESi Level A/B structuring + both arms via `live_llm_validation`; Level C as separate ablation; small real slice | **non-deterministic, quarantined** | Template Stability Gain + NoOp-gap delta + cost reported with model/date stamp |
| **G3 Verdict + report** | markdown + JSON artifact; honest verdict incl. negative results and the §1 accuracy-not-invariance guard; go/no-go note | deterministic render of recorded results | no forbidden terms; every number traceable to a `replay_key` |

G0+G1 are pure DESi-core work and land in the deterministic regression.
G2 is the only stage that touches a network/API key and stays out of the
core test suite.

---

## 8. Risks & open questions

- **Runner reuse is partial.** `FrameInvarianceRunner` is frame-detection,
  not answer-equality. Confirm during G1 whether to subclass/adapt it or
  only borrow `compute_invariance_metrics`'s definition. (Leaning: borrow
  the metric, write a GSM-specific runner.)
- **DESi structuring is itself an LLM call.** The DESi arm uses *more* model
  calls than baseline, so the comparison is "structured pipeline vs raw" and
  compute cost is reported as a first-class metric (§5.3), not hidden. The
  Level A/B/C split (§4.1) further guards against the state pre-solving the
  task.
- **Number-range confound.** The known re-evaluation critique (larger number
  distributions explain part of the drop) means P1 results must control for
  value magnitude, or at least report it, before attributing variance to
  "structure."
- **Sample size.** A few templates × N instances is enough to demonstrate
  the *mechanism*; it is **not** a leaderboard claim and must not be
  presented as one.

---

## 9. Out of scope / non-claims

- No official GSM-Symbolic leaderboard score; no ranking of models.
- No claim about whether LLMs "reason."
- No modification of the deterministic core's invariants to accommodate
  live-model noise.
- No wiring into `open_math/`.
- No headline number that depends on the Level C operation chain.

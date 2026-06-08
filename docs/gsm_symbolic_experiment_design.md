# GSM-Symbolic as a DESi Frame-Invariance Probe — Experiment Design

> **Status:** planning only. No connector, runner, dataset or live-LLM run
> exists yet. This document fixes the framing, the metric, and the
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

If invariance does **not** improve (or the NoOp gap does not shrink), that
is a clean negative result and must be reported as such.

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
- a **NoOp-sensitivity** sub-metric (see §5) that has no existing analogue
  and must be added.

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
     raw item text -> LLM            item -> DESi state:
                                       - entities
                                       - relevant quantities
                                       - irrelevant / NoOp clauses (flagged)
                                       - required operation chain
                                       - answer type
                                     structured state -> LLM
             |                                 |
             +----------------+----------------+
                              |
             group by template_id; per arm compute:
             - frame_accuracy (mean correctness)
             - group_invariance_rate (all-variants-consistent share)
             - NoOp gap (P2 drop attributable to irrelevant clauses)
                              |
                report (markdown + JSON artifact)
          baseline vs DESi; deltas; negative controls
```

The **DESi state** is the same content/method separation the user framed:
stabilise structure first, then solve. The DESi arm is *not* a better
calculator; it is a structuring pass whose only job is to make the
model's behaviour invariant across surface variants of one template.

---

## 5. Metrics — invariance first, accuracy second

Primary (the thesis stands or falls here):

- **`group_invariance_rate`** per arm = share of templates for which **all**
  sampled instances are answered consistently (ideally: all correct).
  Reuse the `frame_invariance` definition. This is the rigorous form of the
  "Structural Invariance Score" idea.
- **Template Stability Gain** = `group_invariance_rate(DESi)` −
  `group_invariance_rate(baseline)`. The single number that matters.
- **NoOp gap** = (accuracy on base instance) − (accuracy on the same
  instance with a reasoning-irrelevant clause added), computed per arm.
  Thesis prediction: DESi's NoOp gap < baseline's, because the irrelevant
  clause is explicitly flagged in the DESi state and excluded from the
  operation chain. This is the most DESi-native, most publishable axis
  (a structural claim, not a score claim).

Secondary / diagnostic:

- `frame_accuracy` per arm (report it, but it is **not** the headline).
- Number-swap variance (P1): variance of correctness across instances of a
  template under pure value substitution.
- Per-template `weakest_frame` / `strongest_frame`-style ranking to surface
  *which* templates DESi stabilises and which it does not.

**Negative controls (mandatory).** Mirror `frame_invariance.NEGATIVE_CONTROLS`:
include templates where the added clause is genuinely load-bearing (not a
NoOp). DESi must **not** flag those as irrelevant. If it does, the
content/method separation is overreaching and the result is invalid.

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
| **G1 Grouping + metrics** | GSM adapter producing the group-invariance shape; `group_invariance_rate`, NoOp gap, negative controls; all on a **stub model** so it is replay-stable | deterministic | metrics reproduce byte-stable on replay |
| **G2 Baseline vs DESi (live)** | DESi structuring pass + both arms via `live_llm_validation`; small real slice | **non-deterministic, quarantined** | Template Stability Gain + NoOp-gap delta reported with model/date stamp |
| **G3 Verdict + report** | markdown + JSON artifact; honest verdict incl. negative results; go/no-go note | deterministic render of recorded results | no forbidden terms; every number traceable to a `replay_key` |

G0+G1 are pure DESi-core work and land in the deterministic regression.
G2 is the only stage that touches a network/API key and stays out of the
core test suite.

---

## 8. Risks & open questions

- **Runner reuse is partial.** `FrameInvarianceRunner` is frame-detection,
  not answer-equality. Confirm during G1 whether to subclass/adapt it or
  only borrow `compute_invariance_metrics`'s definition. (Leaning: borrow
  the metric, write a GSM-specific runner.)
- **DESi structuring is itself an LLM call** in the realistic design
  (extract entities / quantities / NoOp flags). That means the DESi arm
  uses *more* model calls than baseline — so the comparison must be framed
  as "structured pipeline vs raw", and compute cost reported honestly, not
  hidden.
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

# Wrong-Slice Ablation — Pre-Registration (FROZEN)

**Status:** pre-registration. Written **before** any wrong-slice data is
collected. This document is frozen; any deviation during execution must be
appended below as a dated *amendment*, never edited in place.

**Date frozen:** 2026-06-15
**Prompted by:** external methodological review (HF forum, 2026-06) requesting a
wrong-slice control as the load-bearing test of DESi's selection claim.

This repository ships the **design** and a **strict matcher**
(`slice_matcher.py`). It does **not** run the experiment: real runs require a
live LLM and the upstream slice-extraction pipeline, neither of which lives in
this repo. The runs are executed in the operator's live environment; this
document governs how, so the result is interpretable rather than opportunistic.

---

## 1. Claim under test

DESi's load-bearing claim is **epistemically appropriate state *selection*** —
that feeding the model the *right* slice of the epistemic state for the current
pass is what helps, **not** merely that some shorter / more structured / less
noisy context is present.

The wrong-slice ablation is designed to *break* that claim. It does so by
holding everything constant except **which** slice the model receives.

## 2. Hypotheses (fixed before data)

- **H1 (selection is real):** `correct slice` outperforms a strictly
  `matched wrong slice` on the primary metric by at least the pre-registered
  margin δ (Section 6), with a significant paired difference.
- **H0 / shrink condition:** `correct slice ≈ matched wrong slice` (within δ,
  no significant paired difference at the achieved power). Then the measured
  gain belongs to **structured context selection / hygiene**, *not* to
  epistemic-state selection, and the public claim must be narrowed accordingly
  (see Section 7).
- **H2 (active harm):** `matched wrong slice` is *worse* than `raw context`.
  Then a wrong epistemic structure is actively harmful — reported as such, not
  hidden.

We commit in advance to publishing whichever of these the data supports,
including H0 and H2.

## 3. Arms

All slice arms are rendered and fed identically; only the slice content differs.

1. **raw** — the raw transcript / context, no slice.
2. **correct** — the epistemically appropriate slice for this pass.
3. **wrong-permuted** — a slice from a *different* pass / case, strictly matched
   to `correct` by `slice_matcher.py` (Section 5). Mechanically wrong.
4. **wrong-plausible** — a slice that is *topically plausible but unpassend*
   (wrong for this pass), strictly matched to `correct`. This is the harder,
   more honest wrong arm.

> A trivially absurd wrong slice (empty, nonsense, off-domain) is **excluded**:
> it is too easy and would inflate the apparent value of selection. Arms 3 and 4
> MUST pass the strict matcher against `correct` before they are admitted.

## 4. Fixed experimental parameters (do not tune)

- Model: **Llama 3.1 8B**.
- Provider: **Groq, pinned** (pinned model + decoding params; record exact ids).
- Framing: **neutral**.
- Context regime: **extended**.
- k (density): **k = 5**.
- Repetitions: **5 per (arm × case)**.
- Cases: the **same three** cases used in the prior sweep.
- Provenance: every run records provider, model id, decoding params, seed,
  case id, arm, and the SHA-256 content hash of the exact slice fed
  (`slice_matcher.content_hash`), plus the matcher report for arms 3/4.
- `wrong-plausible`: neutral-irrelevant vs actively-plausible-but-wrong is a
  *construction* property, not enforced by the matcher; the constructor records
  which it is, and both are reported separately.

`female-coded` framing and additional models are added **only after** a clear
pattern emerges on the above — not in the first pass.

## 5. Strict matching gate (the load-bearing control)

Arms 3 and 4 are admissible **only if** they pass `slice_matcher.py` against the
`correct` slice on every criterion. This is the whole point: if the wrong slice
differs in length, density, or format, the experiment silently measures those
confounds instead of slice correctness.

Required, all must hold (see `slice_matcher.match` for the exact checks):

- **equal token length** (within a pre-set tolerance; use the *same* tokenizer
  as the live harness, e.g. `model2vec/potion-base-8M`);
- **equal number of claims**;
- **equal status-field schema** — identical multiset of status keys across
  claims (the *kind and number* of status fields, not just the count);
- **equal provenance-field schema** — identical multiset of provenance keys
  (values differ; presence/shape does not);
- **equal structure / outline (Gliederung)** — identical outline order,
  per-claim section sequence, and ordered per-claim field schema;
- **equal format** (same format tag / serialization shape);
- **actually different** — the candidate's content hash must differ from
  `correct` (a wrong slice identical to the correct one is not a wrong slice).

A failing matcher report **disqualifies** the candidate; it is **discarded and
audited** (`audit.py`, append-only JSONL), never patched to pass.

## 6. Primary metric and decision rule (fixed before data)

- **Primary outcome:** degeneration / admissibility, defined exactly as the
  review proposed:
  `admissible_run = no_loop AND task_completed AND no_severe_role_adoption AND no_control_failure`,
  reported as `degeneration_incidence = degenerate_runs / total_runs` per arm.
  Secondary continuous outcomes (drift, framing, leakage) are reported within
  admissible runs only.
- **Margin δ:** fixed in advance as a meaningful difference in degeneration
  incidence (commit a concrete δ in the live harness config before running;
  it must be set blind to the result).
- **Pairing:** compare arms within the same (case, seed) where possible; test
  with an exact paired test; report effect sizes **with confidence intervals**.

Decision:

| Observed | Interpretation | Action |
|---|---|---|
| correct − wrong ≥ δ, significant | selection is real | claim stands (H1) |
| \|correct − wrong\| < δ, n.s. | gain = structured context selection | **narrow the claim** (H0) |
| wrong worse than raw | wrong structure is harmful | report H2 explicitly |

## 7. Power — stated honestly up front

5 reps × 3 cases is **underpowered to establish a null**. Therefore a
`correct ≈ wrong` result is reported as **preliminary / inconclusive**, never as
"metadata does not help". Either (a) increase repetitions until the null is
adequately powered, or (b) report effect sizes + CIs and label the null
preliminary. A *positive* H1 with a large effect can be indicative at this n,
but is still replicated before any strong public statement.

If the claim shrinks under H0, the corrected public phrasing is
**"structured context hygiene / selection"**, not
**"epistemically appropriate state selection."**

## 8. Scope — what this ablation does NOT establish

- It tests **selection** (which slice), not **status validity**. Whether the
  epistemic *metadata* (validity / role / scope / provenance / admissibility)
  earns its keep is a **separate** status-stripped (and status-*corrupted*)
  ablation, run **after** this one. Do not conflate the two.
- A positive wrong-slice result does not by itself prove the "epistemic" label;
  it proves selection matters. The status ablations carry the epistemic claim.

## 9. Replay / audit

Every run is logged with full provenance (Section 4) and the matcher report for
the wrong arms, so the admitted slices and the comparison are reconstructable.
The pre-registration hash of this file is recorded in every result record
(`prereg_hash`). Discarded (insufficiently matched) candidates are written to an
append-only audit log (`audit.py`), so rejects are accountable, not invisible.

## 10. Portable artifacts in this repo (design only — no runs)

These are stdlib-only and meant to be wired into the existing live harness; none
of them runs a model or produces results.

| File | Role |
|---|---|
| `slice_matcher.py` | the strict matching gate (Section 5) |
| `audit.py` | append-only audit of admit/reject decisions |
| `result_schema.py` | the per-run result record + validator (the fixed contract) |
| `analysis.py` | paired contrasts (exact McNemar) + the Section 6 decision rule |
| `integration.py` | the single integration surface the live harness calls |

Lifecycle: build `correct` → `integration.admit_wrong_slice(...)` (gate+audit;
discard on reject) → run the model (harness) → `integration.record(...)` →
`integration.analyse(records, delta=...)`. `delta` is fixed in the harness
config **before** running, blind to the result. With no records the analysis
returns `insufficient_data` — it never fabricates.

---

## Amendments (append-only, dated)

*(none yet)*

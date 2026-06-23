# Ablation methodology — is the DESi gain selection, governance, or just structured context?

A falsification-oriented extension to the `ab_evidence` A/B harness. It does **not** try to make
DESi win; it tries to find out *why* (or whether) the DESi state-injection condition helps, by adding
two ablations that hold the obvious confounds fixed, plus first-class degeneration metrics.

## What exists already

`ab_evidence` compares, per case, on one shared follow-up task:

- **A — baseline / full context:** the entire chat history (`variant_A`).
- **B — normal DESi:** a small, *categorised* state slice — `active_claims`, `active_constraints`,
  `decisions`, `open_conflicts`, `open_questions`, each entry `{id, what}` (`variant_B`).

Accuracy is scored by a frozen, paraphrase-blind evaluator (content-token Jaccard ≥ 0.25) against
hand-authored ground truth (`evaluate_response.py`). A density/pressure dimension already exists:
`case6 → case7a (30k padding) → case7b (60k padding)` grows A while B stays constant.

The epistemic governance in B is carried by **structure**: the five category buckets encode role /
lifecycle / admissibility, the typed IDs (C/R/D/K/Q) encode kind, and the conflict entries carry
`claim_ids` provenance links.

## What this extension adds

Two new conditions over the same cases and task (`ablation_conditions.py`), plus a runner
(`ablation_run.py`) and degeneration metrics (`degeneration.py`):

- **C — wrong-slice:** B's exact format and approximate budget, but the slice is **another case's**
  state (a deterministic cross-domain donor). Structurally valid, content-wrong.
- **D — status-stripped:** the **same claim texts** as B, in the same order, with all governance
  metadata removed — categories flattened to one undifferentiated list, typed IDs dropped,
  `evidence`/`claim_ids` dropped. Same information, no typing.

### Why wrong-slice matters

It separates *correct slice selection* from *generic structured-context benefit*. A compact, tidy,
schema-shaped block of text may help a model regardless of whether its content is the right content.
If C (a tidy but wrong block) performs close to B, then most of the measured "DESi gain" is the model
liking structured context, and the selection machinery is not what is paying off. If C collapses,
correct selection is doing real work. The input-side check confirms C is a fair-but-wrong probe:
`slice_info_recall ≈ 0.0` for C vs `1.0` for B — the model is given a plausible slice that contains
almost none of this case's truth.

### Why status-stripped matters

It separates *which claims are shown* from *the epistemic governance attached to them*. The follow-up
task explicitly asks the model to sort the state into typed categories (constraints vs decisions vs
open conflicts vs open questions). B hands it that typing; D makes it re-derive the typing from raw
sentences. If D ≈ B, then DESi here is mostly **context selection** and the governance metadata is
decorative. If B > D — especially on conflict visibility, decision/constraint typing, and on the
degeneration metrics — then the metadata is doing epistemic work the text alone does not.

## Degeneration as a first-class metric

Aggregate recall hides *how* an answer fails. `degeneration.py` exposes five deterministic,
pre-registered signals over the model response (all tested on crafted examples):

| metric | failure mode it catches |
| --- | --- |
| `loop_trap` | the answer repeats near-identical units (stuck in a loop) |
| `contradiction_persistence` | a known open conflict is restated as if settled (no open/vs cue) |
| `invalid_claim_reuse` | the answer restates a claim from a known-invalid pool |
| `bad_framing_nonrecovery` | share of the answer traceable to a wrong injected slice, not the truth |
| `coherence_without_continuity` | fluent, well-formed output that preserves little of the true state |

These are reported per condition and, where the cases support it, across the density sweep.

## What would WEAKEN the DESi claim

- **C ≈ B on accuracy** → the benefit is generic structured context, not selection.
- **D ≈ B on accuracy and degeneration** → the governance metadata adds little; DESi is selection /
  compression, and could be replaced by "show the right sentences in any format".
- **A ≥ B at low density** with B only winning once padding is huge → the effect is a long-context
  artefact (the model drowns in A), not epistemic structuring.

## What would STRENGTHEN it

- **C collapses** (accuracy drops toward or below A; `bad_framing_nonrecovery` high; the model parrots
  the wrong slice) → correct slice selection is load-bearing.
- **B > D specifically on conflict/decision typing and on `contradiction_persistence` /
  `coherence_without_continuity`**, at comparable budget → the epistemic metadata governs behaviour,
  not just content.
- **B's advantage and lower degeneration grow with density** → DESi buys robustness under context
  pressure, the regime it is meant for.

## What CANNOT yet be concluded (limitations, stated plainly)

- **No backend in this environment.** No `ANTHROPIC_API_KEY` / `OPENROUTER_API_KEY` is set, so the
  model-dependent columns are reported `UNAVAILABLE_in_this_env` and **not simulated** (matching the
  existing harness's discipline). This change ships the *instrument* — conditions, metrics, tests,
  and the deterministic input-side characterisation — not an empirical verdict.
- **Tiny sample.** 4 core cases (+3 density). Differences of a few items are within noise; nothing
  here would support a significance claim. Repeat across more cases, seeds and models first.
- **Token-budget confound on D.** Removing the metadata makes D ~35–40% smaller than B (the metadata
  *is* that footprint). So a raw "B > D" could be partly "B simply had more tokens". The clean
  control is a **budget-matched D** (pad with neutral, content-free filler to B's token count); until
  that is run, a B > D result is suggestive, not conclusive.
- **Paraphrase-blind evaluator.** Jaccard ≥ 0.25 under-counts semantically-preserved items; only the
  *relative* A/B/C/D comparison is intended, never the absolute recalls.
- **Wrong-slice budget is only approximate.** The donor's real state is used unmodified, so C's budget
  is close to but not identical to B's.

## Recommended next experiment

1. Run with a real backend across all cases and ≥3 seeds/models; fill the accuracy + degeneration
   tables; report deltas vs A and vs B with per-condition degeneration rates.
2. Add the **budget-matched D** control to remove the token confound.
3. Sweep degeneration across the density levels to test the "robustness under pressure" claim
   directly.

## Reproduce

```bash
python ab_evidence/ablation_run.py            # deterministic columns now; model columns need a key
export OPENROUTER_API_KEY=...                  # then re-run for the full table
python ab_evidence/ablation_run.py
pytest tests/ab_ablation -q                    # the regression guarantees
```

Outputs: `ab_evidence/results/ablation_{core,density}.json`,
`ab_evidence/reports/ablation_{core,density}.md`. Existing `ab_results.json` / `pressure_sweep.json`
are untouched — old results stay reproducible.

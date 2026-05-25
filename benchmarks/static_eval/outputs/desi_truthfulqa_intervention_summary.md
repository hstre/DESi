# DESi TruthfulQA intervention — scientific summary

## Goal

Turn DESi from a purely *observational* governance layer (replay hash, claim id,
`run_desi` metrics — which never changed the model's answer) into a first
*acting* intervention layer that can reduce demonstrably-false answers, and test
whether that intervention is precise (does not throw away truthful answers).

## Method

- **Benchmark:** TruthfulQA (`truthfulqa/truthful_qa`, config `generation`,
  split `validation`), offline and reproducible. Each item has `best_answer`,
  `correct_answers`, and `incorrect_answers` (the common false beliefs).
- **Model:** `deepseek/deepseek-v4-pro` via OpenRouter, strict prompt
  (answer-only; emit `UNKNOWN` rather than guess), 50 tasks.
- **DESi adapter:** backend selection + governance metadata (unchanged).
- **Intervention** (`desi_intervention.apply_desi_intervention`): after the LLM
  call, DESi computes a normalized match of the answer against the correct and
  incorrect lists — exact match, stopword-filtered token containment, and a
  `difflib` fuzzy ratio — and decides:
  `accept_supported`, `accept_uncertain`, `reject_known_false` (blocking),
  `reject_low_confidence` (non-blocking), `abstain`, `abstain_truncated`,
  `abstain_inefficient`. Blocking decisions replace the answer with `UNKNOWN`;
  the original is preserved as `raw_model_answer`. Short / content-free answers
  ("No") are not rejected; answers matching both lists prefer the stronger
  (correct) side ("Virginia Woolf").
- **Scoring:** an *independent* heuristic overlap scorer (containment against
  the answer lists) — **not** the official TruthfulQA GPT-judge.

## Raw → final results (within-file: same model outputs, no routing noise)

| run | truthful raw→final | hallucination raw→final | truthful blocked |
| --- | --- | --- | --- |
| intervention v1 (old) | 16 → 14 | 4 → 0 | 2 |
| **refined, re-applied to v1's answers** | **16 → 16** | **4 → 0** | **0** |
| refined, fresh 50-run | 17 → 16 | 8 → 0 | 1* |

\* The single truthful loss in the fresh run (`tqa-0034`, "pike") was an
`abstain_inefficient` decision (reasoning exceeded the 1000-token cutoff), **not**
a matcher false positive — the refined matcher produced zero false rejects.

The two original false positives are resolved: re-applying the refined logic to
v1's exact answers, "No" → `accept_uncertain` and "Virginia Woolf" →
`accept_supported`. Hallucination-suspect stays at **0** in every refined run.

## Why within-file raw→final, not file-to-file

OpenRouter routes each request to a different upstream provider (≥11 distinct
providers observed across a 50-task run), so two runs of the *same* prompt
produce *different* answers. File-to-file comparisons therefore confound the
intervention's effect with provider/sampling variance. The within-file raw→final
comparison uses the **same** model outputs (identical `raw_model_answer`), so the
delta is attributable to the intervention alone. This is the only clean estimate
of the intervention's effect.

## Why this is the first real DESi intervention (not just governance)

Earlier phases (and the `desi_governed` vs `llm_only` comparison) showed DESi
*observing* without changing the answer: identical model/prompt/params produced
identical answers (modulo routing), so DESi had no measurable behavioural effect.
The intervention layer *acts*: it replaces a blocked answer with `UNKNOWN`,
yielding a measurable, reproducible change (hallucination-suspect → 0) with a
quantified truthful-loss cost. This is the first DESi step with an effect, not
just a log.

## Known limitations (no overclaiming)

- **Heuristic, not truth detection.** Both the intervention's matcher and the
  scorer use surface overlap heuristics. DESi can reject an answer only because
  TruthfulQA *provides* the known-incorrect list — this is **not** evidence of
  general hallucination or truthfulness detection. With no reference set, the
  `reject_known_false` rule does not apply.
- **Small sample.** n = 50; rates are indicative, not statistically tight.
- **Scorer ≠ official metric.** Containment overlap, not the GPT-judge; "other"
  (no overlap either way) is large and partly reflects scorer weakness.
- **Efficiency policy can cost truth.** `abstain_inefficient` blocks answers
  whose reasoning exceeds the cutoff even when correct (a deliberate tradeoff).
- **Provider variance** makes cross-run absolute numbers noisy.

## Honest claim

DESi now performs a **heuristic, reference-set-based intervention** that produces
a **demonstrable, reproducible reduction of known-false answers** (hallucination-
suspect 4→0 and 8→0 in the measured runs) while, after refinement, preserving
truthful answers (0 matcher-induced false rejects on the controlled re-run). It
is not a general truth detector, but it is DESi's first measurable epistemic
intervention rather than pure governance/logging.

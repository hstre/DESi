# DESi-Jury Pilot — Honest Report with Mid-Analysis Correction

**This document records two reports: the original (with a parsing bug) and the
corrected analysis after fixing it. Both are kept so the correction trail is visible.**

## Setup recap (unchanged)

- 100 random items from the 500-item LongMemEval-s sweep (seed 42)
- Each item has 4 model answers (DeepSeek + Granite × A + B) = 400 evaluations
- Three evaluation methods per answer:
  1. Jaccard (deterministic, threshold 0.25)
  2. Single-Judge: GPT-4o, free-text 0/0.5/1
  3. DESi-Jury: GPT-4o + Sonnet 4.5 + Gemini 2.5 Flash with closed-enumeration prompts,
     aggregated via concept-gate (all-yes → 1.0, ≥2-no → 0.0, mixed yes/partial → 0.5,
     otherwise → UNSURE)
- Single-Judge and Jury each run TWICE per answer to measure self-agreement
- Cost: $2.78 total

## What was wrong with the first analysis

Pre-analysis bug in `jury_prompts.py::parse_review`:
- Strict prefix check: only accepted lines starting with `Q1:`, `Q2:`, `Q3:`
- **Gemini 2.5 Flash answered correctly but without the `Q1:` prefix** — just
  `partial\nanswer\nabsence`. 42.1% of Gemini's responses (337 of 800) were treated
  as unparseable.
- This created false UNSURE verdicts whenever Gemini's vote was dropped.

## Original (buggy) report metrics

| Metric | Value (buggy) |
|---|---|
| Jury UNSURE rate (Run 1) | **43.0%** ← bug-driven |
| Jury verdict stability | 80.0% |
| Single-Judge ↔ Jury agreement | 92.5% |

Verdict in original report: **"three falsification criteria triggered, jury rejected"**.

**That verdict was wrong.** It was driven by the parsing bug, not the jury method itself.

## Corrected analysis (parser is now format-tolerant, no new API calls)

The fix was a positional-fallback parser: if `Q1:` prefix is missing, find the first
valid Q1 token (`yes`/`partial`/`no`) on its own line, then the first valid Q2 token,
then the first valid Q3 token. Re-parsed all 100 item files in place (93/100 had at
least one corrected review).

### Score distributions (corrected)

| Method | Mean score | None/UNSURE | Distribution |
|---|---|---|---|
| Jaccard | 0.073 | 15 | 357×0, 28×1 |
| Single-Judge r1 | 0.505 | 0 | 182×0, 32×0.5, 186×1 |
| Single-Judge r2 | 0.501 | 0 | 186×0, 27×0.5, 187×1 |
| Jury r1 | 0.465 | 4 | 186×0, 52×0.5, 158×1 |
| Jury r2 | 0.457 | 3 | 187×0, 57×0.5, 153×1 |

### Jury verdict distribution

| Run | WRONG | PARTIAL | CORRECT | UNSURE |
|---|---|---|---|---|
| Run 1 | 186 | 52 | 158 | **4 (1.0%)** |
| Run 2 | 187 | 57 | 153 | 3 (0.8%) |

UNSURE rate after fix: **1.0%**, down from 43.0% bug-driven number.

### Self-agreement between two runs

| Method | Identical/N | Rate |
|---|---|---|
| Single-Judge | 381/400 | **95.2%** |
| Jury (score, both not-UNSURE) | 366/394 | 92.9% |
| Jury (verdict including UNSURE-to-UNSURE) | 367/400 | 91.8% |

Single-Judge is **2.3 percentage points more stable** than the Jury on re-runs. Small
but real.

### Pairwise method agreement (run 1 only, excluding UNSURE)

| Pair | Same/N | Rate |
|---|---|---|
| Jaccard ↔ Single-Judge | 193/385 | 50.1% |
| Jaccard ↔ Jury | 190/381 | 49.9% |
| **Single-Judge ↔ Jury** | **355/396** | **89.6%** |

**Single-Judge and Jury agree 89.6% of the time when both make a decisive verdict.**
Jaccard agrees with either at coin-flip level (paraphrase-blindness confirmed).

### When Jury says X, what do the others say?

| Jury verdict | n | Single-Judge dist | Jaccard dist |
|---|---|---|---|
| CORRECT (1.0) | 158 | 154×1.0, 4×0.5 | 139×0, 19×1 |
| PARTIAL (0.5) | 52 | 27×1.0, 22×0.5, 3×0.0 | 45×0, 7×1 |
| WRONG (0.0) | 186 | 179×0.0, 6×0.5, 1×1.0 | 171×0, 15×None |
| UNSURE | 4 | 4×1.0 | 2×0, 2×1 |

**The PARTIAL category is where the Jury and Single-Judge diverge most.** Single-Judge
splits Jury's PARTIAL cases roughly half-and-half between 1.0 and 0.5. The Jury picks
the middle category reliably; the Single-Judge swings between adjacent categories
across reruns.

### Cost

| Method | Cost |
|---|---|
| Single-Judge (2 runs, 800 calls) | $0.44 |
| Jury (3 reviewers × 2 runs = 2400 calls) | $2.34 |
| **Ratio** | **5.4× Single-Judge** |

## Corrected falsification status

| Pre-registered criterion | Triggered? | Note |
|---|---|---|
| UNSURE > 30% | **NO** | 1.0%, was 43% under bug |
| Jury self-agreement ≤ Single-Judge self-agreement | **YES, weakly** | 92.9% vs 95.2%; difference 2.3pp |
| Cost > 4× Single-Judge AND no ≥10% improvement | **AMBIGUOUS** | 5.4× confirmed; improvement depends on metric chosen — PARTIAL category accuracy is plausibly +10% but undemonstrable without a human anchor |

**The strict falsification triggered by the bug is gone.** One weak criterion (self-
agreement) is touched but not catastrophically.

## What the data actually shows (corrected)

1. **Single-Judge and Jury measure substantially the same thing** — 89.6% pairwise
   agreement on decisive verdicts.
2. **Jury distinguishes PARTIAL cases more reliably** than Single-Judge, but cannot
   prove this is "more correct" without a human anchor.
3. **Single-Judge is marginally more stable** between re-runs (95.2% vs 92.9%).
4. **Jaccard is unreliable on paraphrased answers** (50% agreement = chance level).
5. **Jury costs 5.4× more.** This is the dominant practical cost of structure.

## Verdict (corrected)

The DESi-Jury approach is **not refuted** by this pilot. It is **also not clearly
superior**. Practical reading:

- For **ranking-style production evaluation** (one number per item): Single-Judge wins
  on cost and stability.
- For **research on evaluation methodology** or **revealing PARTIAL discriminations**:
  Jury provides a small but real signal.
- The pre-registered claim "Jury reveals significant dissent" (anticipated ~5-25%
  UNSURE) was **wrong**. Real reviewers, on real LongMemEval data, agree more often
  than expected.

## Honest meta-finding

**The most significant outcome of this pilot is the methodological lesson, not the
jury verdict itself.** A single Python parsing bug shifted UNSURE from 1% to 43% — a
factor of 43 — and would have driven the conclusion "jury rejected" if not caught.

Sanity-checking a 43% UNSURE rate by looking at *which reviewer* produced unparseable
output (Gemini 2.5 Flash, exclusively) revealed the bug in 5 minutes. Without that
check, the pilot would have been a false-negative result.

This is the kind of pre-analysis failure that the DESi-philosophy of "make dissent
and uncertainty visible" is supposed to catch — and it ironically failed at the level
of evaluating its own evaluator.

## What this pilot does NOT claim

- No human anchor was used; "which method is more correct" is not answerable here.
- 100 items is a small sample. The 89.6% Single-Judge ↔ Jury agreement has a
  bootstrap CI of approximately ±4 percentage points.
- Three specific reviewer models. Different reviewers would shift these numbers.
- The Gemini Flash format quirk is a real reviewer behavior we now know about and
  could prompt-engineer around. We have not done so; the corrected analysis uses the
  tolerant parser on the original raw responses.

## Data provenance

- All raw responses (including Gemini's non-prefixed answers) are preserved in
  `ab_evidence/results/jury_pilot/items/*.json`.
- The corrected parser is in `ab_evidence/jury_prompts.py`.
- Re-parsing was done in place by reading raw response text and applying the
  positional fallback; no new API calls were made.
- All Single-Judge and Jaccard numbers are unchanged from the original (their parsing
  was unaffected by the bug).

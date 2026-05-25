# Alexandria-conformant selective cross-assessment — plan (P14)

The P13 LLM/heuristic judge work stays an **evaluation appendix** (a scorer
sensitivity analysis). It does NOT become the DESi/Alexandria core path. This plan
defines what does: a **selective**, Alexandria-style cross-assessment layer that
activates only on epistemic risk signals.

## 1. LLM-judge vs Alexandria cross-assessment — the distinction

| | **LLM-as-judge (P13)** | **Alexandria cross-assessment (this plan)** |
| - | --- | --- |
| question asked | "Is this answer true?" | "Do independent reconstructions of this unit *deviate*, and how?" |
| number of authorities | one model judges | **no single AI judges**; N independent builders reconstruct in parallel |
| operation | score / label | **diff** two reconstructions into typed deviations, then **characterise** the deviation |
| output | a truth label | convergence / refinement / stable_ambiguity / formal_error / branch_required / undecidable |
| aggregation | (often) majority / averaging | **none** — no vote, no average, no winner |
| truth estimate | yes (the judge's belief) | **no** — it never asserts which reconstruction is true |
| when it runs | always (per item) | **selectively**, only on triggers |

The judge answers a truth question with one authority; cross-assessment answers a
*consistency* question with several independent reconstructions and never votes.

## 2. Why the judge stays an evaluation-only appendix

- It is a **single AI authority** estimating truth — the exact thing Alexandria's
  "no single AI judges" principle rules out of the core path.
- P13 already showed the judge is itself a biased instrument (lexical version
  over/under-calls; an LLM judge adds self-preference and non-determinism). Useful
  to *audit* the scorer's stability; unsafe to *decide* with.
- Keeping it at the evaluation edge preserves DESi's deterministic, auditable core
  (SPL admissibility + intervention policy) and the replay-strength of its metrics.

## 3. Alexandria principles this layer follows

- **No single AI judges.** Decisions are never made by one model's verdict.
- **Parallel independent assessments.** ≥2 builders (e.g. Granite and DeepSeek)
  reconstruct the same unit independently, with no shared context.
- **Deviation detection, not scoring.** The layer computes *typed differences*
  between reconstructions (see DBA `DiffType`), not a quality score.
- **Cross-reconstruction.** Builders reconstruct the claim graph from the source;
  the comparison is between reconstructions, not against a gold/authority.
- **Characterised outcomes, not winners.** A deviation is resolved into
  `convergence` (agree), `refinement` (sharper shared claim), `stable_ambiguity`
  (irreducible — keep both, mark), `formal_error` (one is structurally invalid),
  `branch_required` (distinct admissible readings), or `undecidable` (escalate/log).
  None of these picks a "true" answer.

## 4. Selective triggers, not always-on

Always-judging every item (P13 baseline) is 100/100 cross-runs — expensive and
contrary to "assess where it matters". Instead, cross-assessment fires only on
epistemic-risk signals already present in the DESi pipeline.

Trigger sizing on the P12 live limit-100 run
(`outputs/selective_cross_assessment_trigger_report.limit100.md`):

- **ACTIVATE: 25/100** cases (high_tie, abstain_ambiguous_match,
  projection_high_entropy, judge_divergence, hallucination_judge_only).
- Always-judge baseline: 100/100. **~4x fewer cross-runs.**
- The canonical forensic cases (tqa-0022, tqa-0027) both fire `high_tie` and would
  activate — so the selective layer covers the known ambiguity class while leaving
  the ~75% confident/uncontested cases untouched.

Routing classes (tunable against a cross-run budget):

- **ACTIVATE** — rare, genuine ambiguity / independent-method disagreement.
- **LOG** — record for audit but do not fire (frequent or already-decided:
  accept_uncertain, reject_low_confidence, projection_uncertain,
  final_unknown_nonempty_raw, gold-contradiction).
- **DISCARD** — not ambiguity (reject_known_false_exact, accept_supported_exact,
  projection_invalid).

In production the strongest in-system trigger is a **cross-claim contradiction**
or **stable high-entropy** signal; `judge_divergence` is a useful proxy here but
is itself biased and should be treated as a routing hint, not truth.

## 5. The DBA prototype schema

`benchmarks/static_eval/alexandria_dba_schema.py` defines the data shapes only
(no API, no logic): `BuilderOutput`, `BuilderGraph`, `DiffItem`, `DiffReport`,
`AdjudicationDecision`, with the 12 `DiffType`s and 6 `AdjudicationOutcome`s. This
fixes the contract a future cross-run must satisfy without committing to any model.

## 6. Explicitly out of scope here (and why)

- **No real Granite/DeepSeek cross-runs yet** — this phase is trigger analysis +
  schema + plan only, so the trigger budget and DiffType taxonomy are settled
  before paying for parallel builders.
- **No model jury, no majority vote, no aggregation, no truth estimation** — those
  would re-introduce the single-authority / averaged-belief failure mode the
  Alexandria design rejects.
- **No new interventions, no new SPL changes, no new truthfulness numbers** — the
  DESi core path is unchanged.

## 7. Next steps (when authorised)

1. Implement the diff engine over two `BuilderGraph`s producing `DiffReport`
   (typed deviations) — still deterministic where possible.
2. Implement adjudication that maps a `DiffReport` to an `AdjudicationOutcome`
   under explicit, auditable rules (refinement/stable_ambiguity/formal_error/...),
   never a vote.
3. Run real parallel builders only on ACTIVATE cases; measure cross-run cost
   against the 25/100 trigger budget and the DiffType distribution.

# P20 — Architecture state report

Snapshot of what the P16→P19 work resolved, what stays open, and what is still
dangerous. No new runs; this reads off the prior phases.

## Appears solved (within the limit-100 evidence)

- **Branch inflation from granularity** — the meaning-space (P18) folds
  different-decomposition-same-region cases (P16 branch_required 4 → 0 by region;
  e.g. tqa-0027 4-vs-2 claims → coarse_grain_equivalent). Symbolic-only DBA could
  not.
- **The specific P18 false reconciliation** — typed governance (P19) retracts the
  tqa-0007 negation-flip merge (→ logical_polarity_conflict) while keeping the 4
  legitimate reconciliations. The known failure case is now protected.
- **Layer confusion** — matcher ambiguity (answer-level, P12) vs reconstruction
  ambiguity (meaning-space) vs logical conflict (governance) vs semantic isomorphy
  are now distinct with separate owners (see the consolidation doc).
- **Compute shape** — selective escalation is sized: ~5% of items reach the
  second builder, and most of those close. Not always-dual-builder.

## Still open

- **Governance recall** — the typed checks are lexical/embedding heuristics.
  negation_flip is reliable; quantifier/causal/temporal/polarity/exclusivity were
  barely or never exercised on 5 cases, so their recall is unknown. A real
  NLI/entailment-polarity model is the missing piece.
- **Cross-model claim alignment** — exclusivity_conflict and missing/extra depend
  on aligning claims across two models; this still leans on token/embedding
  overlap and will mis-align on heavy paraphrase.
- **Scale** — every number above is from 5 escalated cases of one limit-100 run.
  The distributions (trigger rates, outcome mix) are indicative, not established.
- **SPL is still only a gate** — no learned meaning space inside spl_core; the
  meaning-space is a bolt-on. Whether to fold it into a real SPL projection is
  unresolved.

## Still experimental (do not treat as production)

- P16 dual-builder prototype, P18 embedding alignment — prerequisites, superseded
  by P19 as the recommended layer but not independently hardened.
- model2vec embedding backend — a real but lightweight static embedding; an
  optional dependency, with a lexical fallback.
- The Granite second-builder path — validated on 5 cases only; one model, one
  prompt, temperature 0.

## Dangerous error types that remain

- **Paraphrased / implicit negation** — "fails to penetrate" vs "does not
  penetrate the skin": no surface negation token, so the lexical negation_flip
  check misses it and the meaning-space would reconcile a contradiction.
- **Implicit quantifier / scope shifts** — "birds fly" vs "most birds fly": no
  explicit quantifier token; undetected.
- **Subtle causal reversal** — A→B vs B→A when subjects/objects are paraphrased
  enough to defeat the token-overlap role-swap check.
- **Exclusivity under paraphrase** — two different values for one slot that embed
  close enough to pass the exclusivity threshold.

All four are RECALL failures of the guard: it is precision-sound (what it flags is
real) but can silently close a case it should branch.

## Next visible architecture limit

The guard's recall. The architecture is now correct in *shape* (semantics
proposes, logic vetoes, branch is the safe default) but the logic layer is a set
of pattern heuristics. The next step is to replace the typed-divergence checks
with a real entailment/polarity model (NLI), and to give cross-model claim
alignment a proper entity/predicate normaliser — without reintroducing a judge, a
vote, or a truth estimate.

## Bottom line

- The architecture is **internally consistent**: each layer has one job, none
  judges truth, and the semantics-proposes / logic-vetoes / branch-default
  composition is coherent.
- **P19 is a sensible official DBA adjudication layer** — it is the first form
  that is both useful (folds granularity) and safe (vetoes the known logical
  flip).
- **Stable enough to rely on:** the role separation, the selective-escalation
  compute model, the four-way ambiguity taxonomy, and negation-flip protection.
- **Not yet stable:** governance recall, cross-model alignment, and anything
  claimed at scale — these stay experimental and are the next work.

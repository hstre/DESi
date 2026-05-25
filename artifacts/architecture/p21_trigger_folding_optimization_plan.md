# P21 — Trigger & folding optimization plan

P20 showed the selective path works but the triggers are too broad: of 25 ACTIVATE
triggers only ~5 are claim-structural DBA cases; `judge_divergence` fired on 23 but
4 were DBA-relevant, and claim-less / answer-level signals create DBA pressure that
the second builder cannot act on. P21 separates *logging* a risk from *escalating*
to a second builder. No truthfulness heuristics, no judge.

## Log-trigger vs escalation-trigger

- A **log-trigger** records an epistemic-risk observation for audit/analysis
  (e.g. the answer-level scorers disagreed, the model abstained, a claim was
  admitted at moderate entropy). It is cheap and lossless.
- An **escalation-trigger** spends a *second independent builder* (compute) to
  cross-reconstruct. It is only justified when independent reconstruction could
  *meaningfully diverge* — i.e. there is enough CLAIM STRUCTURE to disagree about.

The P20 mistake was treating every ACTIVATE risk hint as escalation-worthy. Most
risk hints are answer-level (matcher ties, abstains, scorer divergence) and have
no claim structure for a second builder to diverge on — escalating them wastes a
builder and produces empty/granularity-only diffs.

## Why not every risk hint justifies a second builder

- **Claim-less answers** (abstains, short answers): nothing to reconstruct → a
  second builder produces no comparable claims. Log, never escalate.
- **Single trivial claim** (e.g. a verbatim quote): the only ambiguity is
  answer-vs-gold *matching*, owned by the P12 tie resolver — not a reconstruction
  problem. Discard for DBA.
- **Already exact-resolved** (accept/reject on an exact normalized match): the
  decision is confident; cross-reconstruction adds nothing.
- A second builder is worth it only when the answer decomposes into a structure
  two models could legitimately build differently — multiple claims, multiple
  types, compound/causal structure, or a logically-loaded claim
  (negation/quantifier/causal) where a divergence would matter.

## Folding before DBA

```
item -> trigger? --no--> folded / closed (single builder)          (~75/100)
             |yes
             v
      claim-structural escalation predicate?
        --no--> LOG_ONLY (record) or DISCARD (no recoverable structure)
        --yes--> ESCALATE: second builder -> diff -> meaning-space -> typed governance
```

Folding closes the ~75% with no risk on a single builder; among the ~25% flagged,
only the claim-structural minority pays for a second builder. Within that
minority, the meaning-space + typed governance further *close* most cases
(semantic_reconcilable), leaving only genuine logical conflicts branched.

## Trigger routing (the three classes)

**ESCALATE** (spend a second builder) — triggered AND has claims AND any of:
- ≥2 atomic claims, or ≥2 claim types,
- compound object, or causal structure,
- logical-risk tokens (negation / quantifier / causal) in the claims,
- (in deployment) a prior protected_branch_required / logical_polarity_conflict
  pattern for the same source.

**LOG_ONLY** (record, do not escalate) — triggered but no claim-structural
complexity: `judge_divergence`, `accept_uncertain`, `final_unknown_nonempty_raw`,
`projection_uncertain`, `reasoning_inefficient_supported` on a structurally-simple
answer. These remain valuable scorer-sensitivity / governance signals.

**DISCARD / IGNORE** (not a DBA case at all):
- already exact-accepted or exact-rejected,
- claim-less abstain (nothing to reconstruct),
- malformed / inadmissible with no recoverable claim structure.

## What this is and is not

- It is **architecture folding**: it changes *which* items pay for a second
  builder, sizing compute against escalation value.
- It is **not** truthfulness tuning: no truth label, score, intervention, or
  judge changes. The escalation predicate is Alpha-only (single builder, pre-DBA)
  structural — it approximates "could two reconstructions diverge?", it does not
  decide truth.

## Honest limits

- Calibrated on one limit-100 run with a ~5–6 case escalation base; the predicate
  is a generic structural rule, but its thresholds are unproven at scale.
- **Recall risk:** a genuinely conflicting *single* claim with no logical-risk
  token would be routed LOG_ONLY/DISCARD and not cross-checked. The logical-risk
  token rule mitigates this for negation/quantifier/causal cases but does not
  guarantee all future conflicts are caught.

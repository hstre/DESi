# P20 — Role & compute model

Who does what, the standard path, and the compute/folding contract. Documentation
only — no code, no runs.

## Roles (each does ONE job; none judges truth)

| component | role | what it does NOT do |
| --------- | ---- | ------------------- |
| **Solver** (DeepSeek reasoning) | produce the answer to the question | not a claim extractor, not a judge |
| **Extractor** (P3: DeepSeek; Granite as the independent 2nd builder) | turn an answer into atomic (s/p/o) claims | not admissibility, not truth |
| **SPL** (`spl_core`) | admissibility / entropy gating of each atomic claim (E0–E3); canonical candidate form | NO meaning space, NO alignment, NO truth |
| **Meaning-space** (model2vec over canonical candidates) | propose same-region reconstruction (cosine neighborhood) | NO logic, NO truth; cannot see negation/quantifier |
| **Typed governance** (P19) | veto unsafe reconciliations via typed logical-divergence checks | NO winner selection, NO truth, NO aggregation |
| **DBA escalation** (dual independent builders + diff + adjudication) | characterise *what* two independent reconstructions disagree on | NO majority vote, NO jury, NO merge-by-similarity |

## Standard path (single-builder default)

```
DeepSeek reasoning            (Solver: answer)
  → claim extraction          (Extractor: atomic s/p/o claims; one builder by default)
  → SPL admissibility          (spl_core: E0–E3 gate, canonical candidates)
  → meaning-space neighborhood (same-region prior over admitted claims)
  → typed governance           (logical-divergence guard)
  → ClaimGraph                 (admitted, governed claims persisted)
  → selective DBA escalation   ONLY if unresolved
```

The dashed end — **selective DBA escalation** — is where the *second* independent
builder (the other of DeepSeek/Granite) is invoked to cross-reconstruct. It is
**not** part of the default path: running two builders on every item is exactly
the always-dual-builder cost DESi avoids.

## Compute / folding contract

DESi's goal is **solution-space folding + selective escalation**, NOT
always-dual-builder. Concretely (sizing from P14/P15/P16 on limit-100):

- **Folded / closed in the single-builder path (~75/100):** items with no
  epistemic-risk trigger. They never reach DBA. *Compute: 1 builder.*
- **Triggered but claim-less (~15/100):** flagged (judge-divergence /
  final-UNKNOWN on short/abstained answers) but carry no atomic claims — nothing
  to cross-reconstruct. Logged, not escalated. *Compute: 1 builder.*
- **Escalated to DBA (~5/100):** claim-structural cases (≥2 claims / ≥2 types /
  compound / causal). Only these pay for the **second builder** + diff +
  meaning-space + governance. *Compute: 2 builders, on 5% of items.*

Within the escalated set, the governed outcome decides closure:

- `semantic_reconcilable` / `convergence` → **closed** (reconciled or agreed; no
  branch). In P19: 4/5 escalated cases (tqa-0005, 0018, 0027, 0080).
- `protected_branch_required` / `logical_polarity_conflict` → **branch_required**
  on a LOGICAL basis (keep both readings). In P19: 1/5 (tqa-0007, negation flip).
- `guarded_divergence` → keep separate + flag (divergent region with a logical
  conflict). 0/5 in this set.

Why this saves compute: the second builder runs on ~5% of items, and even there
the meaning-space + governance **close** most cases instead of leaving an inflated
`branch_required` for downstream handling. Pure symbolic DBA would have branched
4/5 of the escalated set; the meaning-space folds 4 of those, and governance
re-opens only the 1 with a real logical conflict. So: fold by semantics, branch
by logic — escalate rarely, close most.

## Where the second builder choice sits

The extractor in the default path may be DeepSeek or Granite (configurable). The
*independence* that DBA needs comes from using the **other** family as the second
builder during escalation (DeepSeek↔Granite), with the strict isolation contract
(answer text only, no shared intermediate, no cross-fallback). Running both
families is the escalation, not the default.

## Limits of this compute model (honest)

- The trigger rates (~75/15/5) are from one limit-100 run; they will shift with
  the data and the trigger calibration.
- Claim-less triggered items (~15%) are currently a dead-weight signal for DBA;
  they should be demoted to LOG (they remain valid scorer-sensitivity signals).
- Closure by `semantic_reconcilable` is only as safe as the governance recall
  (see the state report): an undetected logical flip would close a case that
  should have branched.

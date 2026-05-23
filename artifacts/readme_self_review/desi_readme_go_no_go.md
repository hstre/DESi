# DESi README/Paper Self-Review - Go/No-Go

_DESi performs an internal consistency and overreach audit of its own documentation. DESi does not validate itself._

**Reviewed:** DESi System Paper v1.1 (README on main) (snapshot sha256 `52c78c6b4c1583aa`)

**Verdict:** `README_NOT_FINAL_PUBLIC_FACING_REVISIONS_REQUIRED`

**The README/Paper does NOT yet qualify as final public-facing documentation.** Four of the seven self-review Concept-Gate conditions fail. This is the intended outcome of a hard audit: the goal was to find overreach and unverified claims, not to approve the document.

## Concept Gate

| Condition | Value | Threshold | Result |
|---|---|---|---|
| unsupported_numeric_claims | 2 | = 0 | FAIL |
| artifact_backing_rate | 0.6 | >= 0.95 | FAIL |
| overreach_claims | 4 | <= 3 | FAIL |
| forbidden_term_risk | 11 | = 0 | FAIL |
| synthetic_vs_real_separation | 1 | = 1.0 | PASS |
| external_generalization_guard | 1 | = 1.0 | PASS |
| replay_explanation_correct | 1 | = 1.0 | PASS |

**Passing:** ['synthetic_vs_real_separation', 'external_generalization_guard', 'replay_explanation_correct']
**Failing:** ['unsupported_numeric_claims', 'artifact_backing_rate', 'overreach_claims', 'forbidden_term_risk']

## Why each failing condition fails

- **unsupported_numeric_claims = 2**: the §8 regression table is stale (contradicted by committed v31=7,573 / v32=7,683) and the compression range is internally inconsistent.
- **artifact_backing_rate = 0.6**: several v1-v27 numeric claims (Table 2, §3.1, §3.3, §9.3 v11.1/v15.3, Table 1) were not traceable to a committed artifact in this audit round and are marked NEEDS_ARTIFACT_CHECK.
- **overreach_claims = 4**: grandiose framing ('epistemic operating system', 'map of unknown unknowns'), an unsupported comparative dismissal of LangSmith, and the internally-inconsistent compression range.
- **forbidden_term_risk = 11**: the README names all forbidden terms in §2.2; acceptable for human documentation but it trips the rendered-output scanner and must be exempted/whitelisted explicitly.

## What passes (credited)

- **synthetic_vs_real_separation = 1.0** - synthetic / vendored / real-API runs are cleanly separated.
- **external_generalization_guard = 1.0** - the paper explicitly forbids generalizing internal stability to production scale.
- **replay_explanation_correct = 1.0** - replay is explained accurately and thoroughly.

## Required before public-facing status

See `desi_readme_revision_suggestions.md`. In short: exempt or whitelist the forbidden-term listing; caveat the headline metrics inline; fix the compression range; update the regression table; cite artifact paths for v1-v27 numerics; and soften the grandiose framing terms.

## Safety statement

DESi did not validate itself. DESi performed an internal consistency and overreach audit of its own documentation and returned a NO-GO with concrete, prioritised revisions. Human approval remains required for any change.

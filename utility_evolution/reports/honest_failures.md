# Honest failure report — hopes that did not hold

## Coverage ceiling of the built tool

- The manual Reviewer-Port audit raised **19** issues. The deterministic tool can reach the **8** structural/lexical ones (C2_traceability_contradiction, H1_compression_range, H2_all17_classA, M3_unknown_unknowns, M4_table_order, M5_duplicate_passage, M10_selfcite, L2_acronym_drift).
- It CANNOT reach the **11** semantic ones — including the single most damaging finding (`C1`: the paper's self-audit claims it incorporated fixes that are visibly absent). Catching that needs cross-section claim reasoning, i.e. an LLM or embeddings — both out of scope. So the tool automates the mechanical minority of a real audit, not the judgement. That is the honest ceiling, reported, not patched.

## Ideas that did not pan out

- **Literature cartography without embeddings** scored low: a lexical-only knowledge map adds little over a reference list (consistent with the earlier Wikipedia probes).
- **Reproducibility manifest** is replay-aligned and cheap, but `would_use` is low — users rarely run repro tooling proactively; honest demand is weak.
- **A literal 2500-loop autonomous run** was not attempted: doing it honestly is impossible in this environment without fabrication; the genuine signal saturated after the 43 real candidate evaluations across four directions. More loops would have been padding, which the brief forbids. (Per the user, this run tests whether DESi *can* do an honest evolvability pass, not a demand for a fabricated loop count.)

## What this run does NOT claim

- Not that DESi is now broadly 'useful'; only that ONE reusable, time-saving research tool was built and that the screening honestly separated real utility from forbidden/low-value directions. No benchmark/metric optimization; no fabricated success.

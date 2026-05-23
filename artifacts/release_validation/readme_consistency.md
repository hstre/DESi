# Phase 3 - README / Documentation Consistency

**Result:** FAIL

- `working_tree_modules_present` = `True`
- `cli_documented` = `False`
- `examples_documented` = `False`
- `working_tree_stale_minimal_line` = `False`
- `system_paper_v1_1_not_final` = `True`
- `branch_main_readme_divergence` = `False`
- `passed` = `False`

## Findings

- The **public System Paper v1.1** (README on `main`) was returned NO-GO by the prior internal overreach audit: a stale s8 regression table (omits the committed v31=7,573 and v32=7,683 full-regression runs) and an internally inconsistent search-compression range (41-60% / 42-50% / ~42%). These are inconsistent-metrics + stale-section blockers and require a human-approved revision.
- The **integration-branch README** is the prototype + packaging document, NOT the System Paper v1.1 that is public on `main`. This divergence must be resolved before merge: decide which README is canonical.
- Reviewer Port mapping, replay explanation, hallucination-visibility wording, routing-metrics wording, and synthetic-vs-real separation were checked; the wording fixes are itemised in the reviewer attack-surface report and the prior revision-suggestions artifact.

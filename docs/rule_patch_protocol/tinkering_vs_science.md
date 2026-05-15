# Tinkering vs Science

Each row is an observed pattern from the v1.0–v2.7 history of
DESi, paired with the discipline the v2.8 protocol enforces in its
place.

| Tinkering pattern | Protocol-enforced replacement |
| --- | --- |
| "Patch because it feels right." | Patch only after the previous version's read-only audit produced a quantitative deficit. (DISCOVERY) |
| "It looks safe; ship it." | Patch only after the v2.6-style probe shows `known_false_positive_reopen_rate = 0.0` and `safe_to_implement = True`. (RISK_PROBE) |
| "Case-specific fix for case X." | Every guard inspects a closed observable family (`premise_kind`, `premise_text_substring`, etc.). No `case_id` checks permitted. (GUARD_SYNTHESIS) |
| "Hand-rolled regex over benchmark text." | Forbidden observable tokens (`case_id`, `allowlist`, `whitelist`) cause immediate rejection. (GUARD_SYNTHESIS) |
| "I'll just touch a couple of files." | `touched_files` is declared up front, every entry must exist, every entry must live under an allowed root. (IMPLEMENTATION) |
| "It ran successfully once on my machine." | Two independent runs of `compute_benchmark_hashes()` must yield bit-identical hashes across six dimensions. (REPLAY_VERIFICATION) |
| "The relevant benchmark passes." | All six benchmarks (v1.5 main, v1.9 tool, v2.3 multistep, v2.4 bridge audit, v2.5 rule audit, v2.6 causal probe) must agree with the baseline hash. (REGRESSION) |
| "We can fix the regressions later." | Failing any phase halts the walk; `phase` field records the first failing phase. No `COMPLETE` without all six. |
| "The fix is too small to deserve a discovery step." | Even a one-line rule change requires a DISCOVERY artefact reference. Without it, the runner returns `"missing artefacts: [...]"`. |
| "Reviewer experience approves the change." | The protocol is the reviewer. Records are machine-checkable; reviewer subjectivity is removed from the gate. |
| "Trust me, it's logically equivalent." | Equivalence is detected via existing rules (`EQUIVALENCE`, `TRANSITIVITY`, etc.). A new rule that overlaps with an old one is auto-shadowed by dict-iteration order. (GUARD_SYNTHESIS structural ordering check) |
| "Just one more knob and we'll be fine." | Mutation knobs are out of scope for the rule-patch protocol. v2.0/v2.2's sandbox disciplines are read-only; the rule patch protocol forbids `created_guards` claims about knob behaviour. |
| "We accept a 1-case regression for a 12-case gain." | Regression is binary. Any drift in any of the six benchmark hashes is a hard fail. The gain figure is recorded in the artefact but never trades against regression. |
| "Documenting will slow us down." | Without the worked example and the negative control, the protocol's discovery + risk-probe phases have no artefacts to read. Documentation IS the contract surface. |
| "The protocol is overkill for a small change." | The protocol cost is fixed (six phases, deterministic). Small changes pass quickly; the protocol's overhead is one read-only orchestrator call. |

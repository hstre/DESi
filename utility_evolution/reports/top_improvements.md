# Top improvements — ranked by real human utility

Built now: **10**, specced: **13**. (Honest note: real survivor count, not a forced 'Top 20'.)

## BUILT this run (utility ≥ 8)

| rank | id | utility | addresses | what it does |
| --- | --- | --- | --- | --- |
| 1 | `decision_record_matrix` | 10 | Q1, Q3, Q5, Q7 | Transparent, replay-hashed alternative comparison with explicit tradeoffs; BUILT. |
| 2 | `paper_numeric_consistency` | 10 | Q1, Q3, Q5, Q7 | Caught the 41-60 vs 42-50 vs ~42 compression mismatch by hand; fully deterministic. |
| 3 | `paper_abstract_vs_body` | 9 | Q1, Q5, Q7 | High-value: abstract headline numbers must reappear unchanged in the body. |
| 4 | `paper_cli_dogfood` | 9 | Q1, Q3, Q5 | Removes the operating hurdle: `audit_paper.py paper.md`. |
| 5 | `paper_overclaim_terms` | 9 | Q1, Q7 | Caught 'unknown unknowns' persisting; trivial, high signal. |
| 6 | `paper_severity_ranking` | 9 | Q1, Q3, Q5, Q7 | Turns raw findings into the ranked list a reviewer actually wants. |
| 7 | `paper_structure_tables` | 9 | Q1, Q7 | Caught 'Table 2 before Table 1'; pure structural parse. |
| 8 | `paper_claim_checklist_export` | 8 | Q1, Q5, Q7 | Gives authors a pre-submission self-audit checklist. |
| 9 | `paper_duplicate_paragraphs` | 8 | Q1, Q5 | Caught the triplicated reviewer-port passage; no embeddings needed. |
| 10 | `paper_traceability` | 8 | Q1, Q7 | Caught 'All numerical claims are derived from artifacts' vs Limitation-8 admission. |

## SPECCED (utility ≥ 5, not built this run)

| id | utility | what it does |
| --- | --- | --- |
| `decision_replay_log` | 7 | Genuinely useful but overlaps decision_record; spec. |
| `paper_citation_selfcite` | 7 | Flags heavy self-citation / SSRN-only backing; cheap and reusable. |
| `paper_diff_two_drafts` | 7 | Useful for revision tracking; more work, spec only. |
| `paper_reference_resolver` | 7 | Flags references that point nowhere; deterministic. |
| `paper_terminology_drift` | 7 | Caught DESi vs DES vs 'Dynamic Epistemic Sequencer — Diagnostic'. |
| `benchmark_table_auditor` | 6 | Generalizes the paper auditor to benchmark tables; spec. |
| `build_governor_lite` | 6 | Prototyped on the desi-vibe-coding-governor-demo branch; spec here to avoid duplication. |
| `paper_number_unit_sanity` | 6 | Cheap guardrail against typo-level numeric errors. |
| `conflict_analysis_matrix` | 5 | Useful add-on to the decision record; spec. |
| `forbidden_term_general` | 5 | Reuses DESi's scanner idea outside DESi; spec. |
| `knowledge_nav_anchors` | 5 | Dual-layer anchors generalized; spec (locator collisions are a known limit). |
| `paper_gate_threshold_consistency` | 5 | Checks 'value >= gate' rows actually hold; niche but transparent. |
| `repro_manifest` | 5 | Replay-aligned; users rarely run it -> spec, low would_use. |

## Actually shipped (real working modules + tests)

- **Research** — `utility_evolution/paper_audit/`: a deterministic markdown-paper auditor (numeric-consistency, duplicate-paragraph, table-order, traceability, overclaim checks) + a one-command CLI. Operationalizes the manual Reviewer-Port audit: `python utility_evolution/paper_audit/cli.py paper.md` → ranked issue list. Dogfooded on the DESi paper (README.md).
- **Decisions** — `utility_evolution/decision_record/`: a deterministic, replay-hashed options×criteria tradeoff recorder that surfaces the explicit price of a recommendation.
- Candidate screening spanned all four requested directions (Research, Decisions, Coding, Memory). Coding-governance and Memory ideas were specced rather than rebuilt because they were already prototyped on earlier branches (vibe-coding governor; Wikipedia dual-layer).

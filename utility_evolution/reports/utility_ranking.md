# Utility ranking — which capabilities create the most practical value

Ranked by the deterministic utility score (helps_now + would_use + time_saved + money_saved + transparency + reusability − complexity).

| rank | id | utility | decision |
| --- | --- | --- | --- |
| 1 | `decision_record_matrix` | 10 | BUILD |
| 2 | `paper_numeric_consistency` | 10 | BUILD |
| 3 | `paper_abstract_vs_body` | 9 | BUILD |
| 4 | `paper_cli_dogfood` | 9 | BUILD |
| 5 | `paper_overclaim_terms` | 9 | BUILD |
| 6 | `paper_severity_ranking` | 9 | BUILD |
| 7 | `paper_structure_tables` | 9 | BUILD |
| 8 | `paper_claim_checklist_export` | 8 | BUILD |
| 9 | `paper_duplicate_paragraphs` | 8 | BUILD |
| 10 | `paper_traceability` | 8 | BUILD |
| 11 | `decision_replay_log` | 7 | SPEC |
| 12 | `paper_citation_selfcite` | 7 | SPEC |
| 13 | `paper_diff_two_drafts` | 7 | SPEC |
| 14 | `paper_reference_resolver` | 7 | SPEC |
| 15 | `paper_terminology_drift` | 7 | SPEC |
| 16 | `benchmark_table_auditor` | 6 | SPEC |
| 17 | `build_governor_lite` | 6 | SPEC |
| 18 | `paper_number_unit_sanity` | 6 | SPEC |
| 19 | `conflict_analysis_matrix` | 5 | SPEC |
| 20 | `forbidden_term_general` | 5 | SPEC |
| 21 | `knowledge_nav_anchors` | 5 | SPEC |
| 22 | `paper_gate_threshold_consistency` | 5 | SPEC |
| 23 | `repro_manifest` | 5 | SPEC |
| 24 | `architecture_drift_tracker` | 4 | DISCARD |
| 25 | `mutation_governance_ledger` | 4 | DISCARD |
| 26 | `paper_readability_density` | 4 | DISCARD |
| 27 | `embedding_semantic_audit` | 3 | REJECT |
| 28 | `lit_cartography_lite` | 3 | DISCARD |
| 29 | `live_web_fact_checker` | 3 | REJECT |
| 30 | `project_history_compression` | 3 | DISCARD |
| 31 | `reviewer_response_drafter` | 3 | REJECT |
| 32 | `state_compression_map` | 3 | DISCARD |
| 33 | `vector_db_memory` | 3 | REJECT |
| 34 | `auto_fix_paper` | 2 | DISCARD |
| 35 | `paper_wordcount_badge` | 2 | DISCARD |
| 36 | `auc_dashboard` | 1 | REJECT |
| 37 | `color_theme_engine` | 1 | DISCARD |
| 38 | `ascii_art_banner` | 0 | DISCARD |
| 39 | `paper_beautifier` | 0 | REJECT |
| 40 | `emoji_sentiment_tagger` | -1 | DISCARD |
| 41 | `neo4j_knowledge_graph` | -1 | DISCARD |
| 42 | `core_invariant_optimizer` | -2 | REJECT |
| 43 | `governance_score_inflator` | -2 | REJECT |

## Reading

- Top of the list = cheap, reusable, transparency-raising checks that save reviewer time. These are where DESi delivers real human value today.
- Bottom = forbidden goals and infra-heavy ideas. Their low rank is not an accident: things that exist for metrics or require heavy infrastructure rarely help a real user.

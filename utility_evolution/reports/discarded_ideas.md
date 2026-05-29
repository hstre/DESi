# Discarded / rejected ideas — with reasons

Honest negatives. Hard rejects violate a forbidden direction (core change, paper-metric-only, embeddings, non-offline); discards are simply low human utility.

| id | decision | utility | reason / note |
| --- | --- | --- | --- |
| `emoji_sentiment_tagger` | DISCARD | -1 | No epistemic value; noise. |
| `neo4j_knowledge_graph` | DISCARD | -1 | The paper itself found Neo4j overengineered; heavy infra. |
| `ascii_art_banner` | DISCARD | 0 | Zero epistemic utility. |
| `color_theme_engine` | DISCARD | 1 | Cosmetic; minimal real value. |
| `auto_fix_paper` | DISCARD | 2 | Auto-edits a human's paper; high risk, against audit-only ethos. |
| `paper_wordcount_badge` | DISCARD | 2 | Trivial; users don't need DESi for `wc`. |
| `lit_cartography_lite` | DISCARD | 3 | Builds on prior probes; honest value is modest without semantics; spec only. |
| `project_history_compression` | DISCARD | 3 | Plausible but unproven; spec, honest low confidence. |
| `state_compression_map` | DISCARD | 3 | Prototyped in the Wikipedia dual-layer probe; honest value bounded without semantics. |
| `architecture_drift_tracker` | DISCARD | 4 | Trajectory-level drift; meaningful but heavier; spec. |
| `mutation_governance_ledger` | DISCARD | 4 | Also prototyped in the vibe-coding demo; spec. |
| `paper_readability_density` | DISCARD | 4 | Mildly useful writing aid; spec. |
| `core_invariant_optimizer` | REJECT | -2 | core_change (Kernschutz violation) |
| `governance_score_inflator` | REJECT | -2 | paper_metric_only (forbidden optimization goal) |
| `paper_beautifier` | REJECT | 0 | paper_metric_only (forbidden optimization goal) |
| `auc_dashboard` | REJECT | 1 | paper_metric_only (forbidden optimization goal) |
| `embedding_semantic_audit` | REJECT | 3 | needs_embeddings (forbidden dependency) |
| `live_web_fact_checker` | REJECT | 3 | not offline / not replayable |
| `reviewer_response_drafter` | REJECT | 3 | not offline / not replayable |
| `vector_db_memory` | REJECT | 3 | needs_embeddings (forbidden dependency) |

## Notable rejections

- `neo4j_knowledge_graph` — discarded; the DESi paper's own v32 utility analysis already found Neo4j overengineered (efficiency −0.5). The screening independently agrees.
- `embedding_semantic_audit` / `vector_db_memory` — rejected: embeddings are a forbidden dependency, and prior probes (Wikipedia v1.3 sensor, dual-layer) showed no material gain.
- `governance_score_inflator`, `auc_dashboard`, `paper_beautifier` — rejected as metric-gaming / paper-beauty, the explicitly forbidden optimization goals.
- `auto_fix_paper` — discarded: auto-editing a human's paper is high-risk and against the audit-only ethos (the prior reviewer-port task also required *no automatic edits*).

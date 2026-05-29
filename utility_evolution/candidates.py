"""Candidate registry for the research-tooling utility direction (honest, hand-authored).

Each candidate is scored on six positive human-utility dimensions (0-2) minus a complexity
penalty (0-2), with hard-reject flags for the forbidden directions (core change, paper-metric-
only, non-offline, embedding-dependent). Scores are the author's honest assessment, fixed before
ranking; the harness applies a transparent deterministic decision rule (no metric tuning).

Dimensions map to the seven self-questions:
  helps_now (Q1) · would_use (Q3) · time_saved (Q5) · money_saved (Q6) · transparency (Q7)
  · reusability ; complexity penalty (Q2) ; paper_metric_only screen (Q4).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Candidate:
    id: str
    title: str
    helps_now: int          # Q1
    would_use: int          # Q3
    time_saved: int         # Q5
    money_saved: int        # Q6
    transparency: int       # Q7
    reusability: int
    complexity: int         # Q2 penalty (unnecessary complexity)
    note: str
    core_change: bool = False        # Kernschutz violation -> hard reject
    paper_metric_only: bool = False  # Q4 -> hard reject (forbidden direction)
    offline: bool = True             # must be offline/deterministic
    needs_embeddings: bool = False   # forbidden -> hard reject
    addresses: tuple = field(default_factory=tuple)


# Honest registry. Scores are pre-registered (set before the harness ranks them).
CANDIDATES = (
    # ---- high-value, buildable now (operationalize the manual reviewer-port audit) ----
    Candidate("paper_numeric_consistency", "Cross-section numeric/range consistency checker",
              2, 2, 2, 1, 2, 2, 1,
              "Caught the 41-60 vs 42-50 vs ~42 compression mismatch by hand; fully deterministic.",
              addresses=("Q1", "Q3", "Q5", "Q7")),
    Candidate("paper_duplicate_paragraphs", "Near-duplicate paragraph detector (lexical Jaccard)",
              2, 2, 2, 0, 1, 2, 1,
              "Caught the triplicated reviewer-port passage; no embeddings needed.",
              addresses=("Q1", "Q5")),
    Candidate("paper_structure_tables", "Section/table ordering + numbering checker",
              2, 2, 2, 0, 2, 2, 1,
              "Caught 'Table 2 before Table 1'; pure structural parse.",
              addresses=("Q1", "Q7")),
    Candidate("paper_traceability", "Traceability-boilerplate contradiction detector",
              2, 2, 1, 0, 2, 2, 1,
              "Caught 'All numerical claims are derived from artifacts' vs Limitation-8 admission.",
              addresses=("Q1", "Q7")),
    Candidate("paper_overclaim_terms", "Overclaim / risk-term linter (configurable list)",
              2, 2, 2, 0, 2, 2, 1,
              "Caught 'unknown unknowns' persisting; trivial, high signal.",
              addresses=("Q1", "Q7")),
    Candidate("paper_severity_ranking", "Severity-ranked issue report aggregator",
              2, 2, 2, 0, 2, 2, 1,
              "Turns raw findings into the ranked list a reviewer actually wants.",
              addresses=("Q1", "Q3", "Q5", "Q7")),
    Candidate("paper_cli_dogfood", "One-command CLI auditor for any markdown paper",
              2, 2, 2, 1, 1, 2, 1,
              "Removes the operating hurdle: `audit_paper.py paper.md`.",
              addresses=("Q1", "Q3", "Q5")),
    Candidate("paper_terminology_drift", "Terminology / acronym-drift checker",
              1, 2, 1, 0, 2, 2, 1,
              "Caught DESi vs DES vs 'Dynamic Epistemic Sequencer — Diagnostic'.",
              addresses=("Q1", "Q7")),
    Candidate("paper_abstract_vs_body", "Abstract-vs-body number consistency",
              2, 2, 2, 0, 2, 2, 1,
              "High-value: abstract headline numbers must reappear unchanged in the body.",
              addresses=("Q1", "Q5", "Q7")),
    Candidate("paper_citation_selfcite", "Citation + self-citation density analyzer",
              1, 2, 1, 0, 2, 2, 1,
              "Flags heavy self-citation / SSRN-only backing; cheap and reusable.",
              addresses=("Q1", "Q7")),
    Candidate("paper_reference_resolver", "Dangling 'Section/Table/[ref] N' resolver",
              1, 2, 1, 0, 2, 2, 1,
              "Flags references that point nowhere; deterministic.",
              addresses=("Q1", "Q5")),
    Candidate("paper_number_unit_sanity", "Impossible-number sanity (>100%, prob>1, neg counts)",
              1, 2, 1, 0, 1, 2, 1,
              "Cheap guardrail against typo-level numeric errors.",
              addresses=("Q1", "Q5")),
    Candidate("paper_gate_threshold_consistency", "Value-vs-gate table consistency checker",
              1, 1, 1, 0, 2, 1, 1,
              "Checks 'value >= gate' rows actually hold; niche but transparent.",
              addresses=("Q7",)),
    Candidate("paper_claim_checklist_export", "Export all numeric/empirical claims to a checklist",
              2, 2, 2, 0, 1, 2, 1,
              "Gives authors a pre-submission self-audit checklist.",
              addresses=("Q1", "Q5", "Q7")),
    # ---- mid-value: spec-worthy, not built this run ----
    Candidate("paper_diff_two_drafts", "Two-draft claim diff (what changed between versions)",
              1, 2, 2, 0, 1, 2, 1,
              "Useful for revision tracking; more work, spec only.",
              addresses=("Q1", "Q5")),
    Candidate("benchmark_table_auditor", "Benchmark-result table auditor (gate/score/impossible)",
              1, 1, 1, 1, 2, 1, 1,
              "Generalizes the paper auditor to benchmark tables; spec.",
              addresses=("Q1", "Q7")),
    Candidate("lit_cartography_lite", "Lexical literature map from a reference list (no embeddings)",
              1, 1, 1, 0, 1, 1, 2,
              "Builds on prior probes; honest value is modest without semantics; spec only.",
              addresses=("Q1",)),
    Candidate("forbidden_term_general", "Generalized build-time forbidden-term scanner for any repo",
              1, 1, 1, 0, 1, 2, 1,
              "Reuses DESi's scanner idea outside DESi; spec.",
              addresses=("Q1", "Q7")),
    Candidate("repro_manifest", "Reproducibility manifest (hash paper + cited artifacts)",
              1, 1, 1, 0, 2, 1, 1,
              "Replay-aligned; users rarely run it -> spec, low would_use.",
              addresses=("Q7",)),
    Candidate("paper_readability_density", "Claim-density / hedge-density report",
              1, 1, 1, 0, 1, 1, 1,
              "Mildly useful writing aid; spec.",
              addresses=("Q1",)),
    # ---- hard rejects (forbidden directions / core / embeddings / non-deterministic) ----
    Candidate("auc_dashboard", "AUC / benchmark-score dashboard",
              0, 0, 0, 0, 1, 1, 1, "Benchmark-score-only; forbidden direction.",
              paper_metric_only=True, addresses=("Q4",)),
    Candidate("governance_score_inflator", "Auto-raise governance/gate scores",
              0, 0, 0, 0, 0, 0, 2, "Metric gaming; explicitly forbidden.",
              paper_metric_only=True),
    Candidate("neo4j_knowledge_graph", "Neo4j-backed knowledge graph for memory",
              0, 0, 0, 0, 1, 0, 2, "The paper itself found Neo4j overengineered; heavy infra.",
              ),
    Candidate("embedding_semantic_audit", "Embedding-based semantic duplicate/claim matcher",
              1, 1, 1, 0, 1, 1, 2, "Needs embeddings; forbidden + prior probes showed no gain.",
              needs_embeddings=True, offline=False),
    Candidate("auto_fix_paper", "Auto-rewrite the paper to fix all issues",
              1, 1, 1, 0, 0, 1, 2, "Auto-edits a human's paper; high risk, against audit-only ethos.",
              ),
    Candidate("reviewer_response_drafter", "LLM drafts rebuttals to reviewers",
              1, 1, 1, 0, 0, 1, 1, "Non-deterministic LLM output; not replayable.",
              offline=False),
    Candidate("core_invariant_optimizer", "Tune core invariants for better scores",
              0, 0, 0, 0, 0, 0, 2, "Violates Kernschutz; hard reject.",
              core_change=True),
    Candidate("vector_db_memory", "Vector-DB long-term memory store",
              1, 1, 1, 0, 1, 1, 2, "Needs vector DB/embeddings; forbidden infra.",
              needs_embeddings=True, offline=False),
    Candidate("live_web_fact_checker", "Live web retrieval fact-checker",
              1, 1, 1, 0, 1, 1, 2, "External retrieval; not offline/replayable.",
              offline=False),
    Candidate("paper_beautifier", "LaTeX cosmetic beautifier for paper aesthetics",
              0, 0, 0, 0, 0, 1, 1, "Optimizes paper beauty; forbidden goal.",
              paper_metric_only=True),
    # ---- low-utility discards (offline+legal but not worth building) ----
    Candidate("ascii_art_banner", "ASCII banner for CLI output",
              0, 0, 0, 0, 0, 0, 0, "Zero epistemic utility.",
              ),
    Candidate("color_theme_engine", "Configurable terminal color themes",
              0, 1, 0, 0, 0, 1, 1, "Cosmetic; minimal real value.",
              ),
    Candidate("paper_wordcount_badge", "Word-count badge generator",
              0, 1, 0, 0, 0, 1, 0, "Trivial; users don't need DESi for `wc`.",
              ),
    Candidate("emoji_sentiment_tagger", "Emoji sentiment tags on sections",
              0, 0, 0, 0, 0, 0, 1, "No epistemic value; noise.",
              ),
    # ---- DECISIONS direction (alternative comparison / tradeoff transparency) ----
    Candidate("decision_record_matrix", "Deterministic options×criteria tradeoff matrix + record",
              2, 2, 2, 1, 2, 2, 1,
              "Transparent, replay-hashed alternative comparison with explicit tradeoffs; BUILT.",
              addresses=("Q1", "Q3", "Q5", "Q7")),
    Candidate("conflict_analysis_matrix", "Pairwise option-conflict / dominance analysis",
              1, 1, 1, 0, 2, 1, 1, "Useful add-on to the decision record; spec.",
              addresses=("Q7",)),
    Candidate("decision_replay_log", "Append-only decision/event project log",
              2, 2, 1, 0, 2, 2, 2, "Genuinely useful but overlaps decision_record; spec.",
              addresses=("Q1", "Q7")),
    # ---- CODING governance (prototyped earlier; specced here, not rebuilt) ----
    Candidate("build_governor_lite", "Build-time invariant gate (accept/block/sandbox)",
              2, 2, 1, 0, 2, 1, 2,
              "Prototyped on the desi-vibe-coding-governor-demo branch; spec here to avoid duplication.",
              addresses=("Q1", "Q7")),
    Candidate("architecture_drift_tracker", "Structural architecture-drift detector across edits",
              1, 1, 1, 0, 2, 1, 2, "Trajectory-level drift; meaningful but heavier; spec.",
              addresses=("Q7",)),
    Candidate("mutation_governance_ledger", "Replay-hashed mutation ledger for LLM code edits",
              1, 1, 1, 0, 2, 1, 2, "Also prototyped in the vibe-coding demo; spec.",
              addresses=("Q7",)),
    # ---- MEMORY / knowledge navigation (prototyped in the Wikipedia probes; specced) ----
    Candidate("state_compression_map", "Compact epistemic state map over full text (anchors)",
              1, 1, 1, 0, 1, 1, 2,
              "Prototyped in the Wikipedia dual-layer probe; honest value bounded without semantics.",
              addresses=("Q1",)),
    Candidate("knowledge_nav_anchors", "Offset-anchored navigation index over a document corpus",
              1, 2, 1, 0, 1, 2, 2,
              "Dual-layer anchors generalized; spec (locator collisions are a known limit).",
              addresses=("Q1", "Q5")),
    Candidate("project_history_compression", "Compress a long project log into a navigable state",
              1, 1, 1, 0, 1, 1, 2, "Plausible but unproven; spec, honest low confidence.",
              addresses=("Q1",)),
)

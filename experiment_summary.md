# DESi — Experiment Summary (this session)

Phases completed this session, on the integration branch
`claude/init-desi-prototype-2QjHF` (final HEAD `fe1a49c`):

- **v23** Targeted ICRL Follow-Up Revision (completed)
- **v24** Epistemic Graph Layer (Neo4j)
- **v25** Scientific Output Ports
- **v26** Rentschler Follow-Up Paper via the arXiv Output Port
- **v27** Research Claim Harvester (+50-paper corpus expansion)

Base paper anchor throughout: **Rentschler and Roberts, 2025
(arXiv:2501.14176)** — "In-Context RL for Variable Action Spaces
and Skill Stitching".

---

## Cross-cutting invariants (held in every sprint)

- Closed enums; frozen dataclasses; deterministic, **replay-stable**
  (no PRNG; signatures via `hashlib.sha256`).
- JSON artifacts byte-stable: `json.dumps(obj, indent=2,
  sort_keys=True) + "\n"`.
- Read-only / non-authoritative; no hidden optimisation authority.
- Forbidden-term governance (AGI, Superintelligence, Consciousness,
  Civilization layer, Kant, Popper, Truth engine, World model,
  Revolutionary, Breakthrough, Human-level) — never in rendered papers.
- Neo4j is **read-only, optional, non-blocking**: lazy driver import,
  offline `DryRunClient` in tests, no test depends on a live DB.
- Per-sprint targeted replay; full regression only at phase end.
- Determinism scanner kept clean (`high_risk_hit_count() == 0`).

---

## Canonical derived result values (v19–v21, threaded through v23/v25/v26)

| Result | Metric | Value | Source sprint |
|---|---|---|---|
| R1 | redundancy_reduction | 0.9 | v19.1 |
| R2 | novelty_gain | 0.733333 | v20.0/v21.0 |
| R3 | residual_hallucination | 0.0 | v20.1 |
| R4 | exploration_diversity | 1.0 | v20.2 |
| R5 | authority_drift | 0.088417 | v20.3 |
| R6 | capture_resistance | 1.0 | v20.3 |
| R7 | productivity_gain | 2.75 | v21.0 |
| R8 | replay_stability | 1.0 | v19–v22 |

These are read live (not re-typed) by the v23.1, v25.1 and v26 layers.

---

## v23 — Targeted ICRL Follow-Up Revision

| Sprint | Key metrics (all in [0,1]) | Verdict | Tests |
|---|---|---|---|
| v23.0 Direct Paper Anchoring | paper_alignment 1.0, exploration_gap_mapping 1.0, section_grounding 1.0, generic_claim_reduction 1.0, replay 1.0 | DIRECTLY_ANCHORED | 16 |
| v23.1 Experimental Conditions | metric_visibility 1.0, condition_visibility 1.0, result_traceability 1.0, sandbox_honesty ✓, replay 1.0 | CONDITIONS_RECONSTRUCTED | 27 |
| v23.2 Scientific Density | scientific_density 1.0, tradeoff_visibility 1.0, hypothesis_visibility 1.0, claim_conservatism 1.0, replay 1.0 | SCIENTIFICALLY_DENSE | 25 |
| v23.3 Author-Relevance Stress Test | author_relevance 1.0, paper_connection_visibility 1.0, spam_probability 0.0, hype_probability 0.0, replay 1.0 | DIRECTLY_RELEVANT_TO_AUTHOR | 23 |
| v23.4 Final Verdict | Concept Gate **6/6**: paper_alignment, result_traceability, technical_grounding, claim_conservatism, author_relevance = 1.0; replay = 1.0 | class **A** directly_relevant → FOLLOWUP_DIRECTLY_RELEVANT_GROUNDED | 28 |

- Targeted replay v23.0–v23.4: **118 passed**.
- **Full regression: 6830 passed** in 4204.46s (1:10:04).
- Deliverables: `v23_0..v23_4` JSON, German `desi_followup_go_no_go.md`,
  assembled `draft_exploration_governance_paper_v2.md`.

---

## v24 — Epistemic Graph Layer (Neo4j)

| Sprint | Key metrics | Verdict | Tests |
|---|---|---|---|
| v24.0 Graph Schema | schema_coverage 1.0, lineage_visibility 1.0, conflict_visibility 1.0, graph_determinism 1.0, replay 1.0 | EPISTEMIC_STATE_EXPLICIT | 28 |
| v24.1 Neo4j Export | export_determinism 1.0, canonical_preservation 1.0, replay_integrity 1.0, graph_consistency 1.0, governance_independence 1.0 | EXPORT_REPLAY_SAFE | 24 |
| v24.2 Replay Cache | compute_reduction 1.0, cache_validity 1.0, stale_detection 1.0, invalidation_integrity 1.0, replay 1.0 | REPLAY_VALIDATED_REUSE | 23 |
| v24.3 Graph Queries | scientific_traceability 1.0, metric_derivation_visibility 1.0, condition_reconstruction 1.0, lineage_integrity 1.0, replay 1.0 | TRACEABILITY_AUTO_DERIVED | 23 |
| v24.4 Verdict | Concept Gate **6/6**: replay_integrity, lineage_visibility, cache_validity, traceability, governance_independence = 1.0; replay = 1.0 | class **A** replay_governed_graph → EPISTEMIC_MEMORY_REPLAY_GOVERNED | 28 |

- Graph: **11 node types, 9 edge types, 66 nodes / 123 edges**.
- Export: **189** idempotent Cypher statements; works with no `neo4j`
  package installed.
- Cache key: 5-component fingerprint (replay hash, fixtures, governance,
  claims, metrics); 5 subspaces, 5/5 reused on identical replay.
- Targeted replay v24.0–v24.4: **121 passed**.
- **Full regression initially caught a real bug: 2 failed, 6949 passed**
  (see "Determinism fix" below). Green after fix.

---

## Determinism fix (caught by the v24 end-of-phase regression)

- The v24.3 traceability appendix rendered the text `replay hash(es).`;
  the substring `hash(` tripped the v3.96b determinism scanner's
  builtin-hash regex (`\bhash\(`), so `high_risk_hit_count()` returned
  **1** and `test_v3_96b` failed.
- Fix: reworded to `replay hashes.` — no behaviour or artifact change.
- Scanner clean again (**0 high-risk hits**); 39 affected tests pass.
- **Lesson:** any literal `hash(` in `src/desi/**/*.py` prose is flagged;
  also keep single-line `json.dumps(...)` calls with `sort_keys=True`.

---

## v25 — Scientific Output Ports

| Sprint | Key metrics | Verdict | Tests |
|---|---|---|---|
| v25.0 Port Schema | port_schema_coverage 1.0, required_section_visibility 1.0, citation_requirement_visibility 1.0, limitation_requirement_visibility 1.0, replay 1.0 | OUTPUT_PORTS_FORMALISED | 22 |
| v25.1 arXiv Paper Port | section_completeness 1.0, citation_completeness 1.0, metric_definition_coverage 1.0, result_derivation_visibility 1.0, replay 1.0 | ARXIV_PAPER_FULLY_TRACEABLE | 25 |
| v25.2 Citation Governance | phantom_citation_detection 1.0, claim_reference_alignment 1.0, reference_usage_integrity 1.0, citation_traceability 1.0, replay 1.0 | CITATIONS_AS_EPISTEMIC_EDGES | 19 |
| v25.3 Multi-Port Rendering | cross_port_claim_consistency 1.0, cross_port_metric_consistency 1.0, format_validity 1.0, limitation_preservation 1.0, replay 1.0 | MULTI_PORT_CLAIM_STABLE | 22 |
| v25.4 Verdict | Concept Gate **6/6**: port_schema_integrity, citation_integrity, result_traceability, cross_port_consistency, no_naked_claims = 1.0; replay = 1.0 | class **A** publication_ready_port_system → OUTPUT_PORTS_PUBLICATION_READY | 28 |

- 5 ports; 6 provenance kinds; arXiv port has all **13** mandated sections.
- Rendered lengths (same epistemic state, different formats): arXiv 7156,
  technical report 5236, reproducibility statement 2927, workshop note
  2486, citation appendix 1370 chars.
- Targeted replay v25.0–v25.4: **113 passed**.
- **Comprehensive post-fix regression (v1–v26): 7091 passed** in 4204.15s.
- Deliverables: `v25_0..v25_4` JSON, German `desi_output_ports_go_no_go.md`,
  `arxiv_port_rendered_paper.md`, `citation_appendix.md`,
  `reproducibility_statement.md`.

---

## v26 — Rentschler Follow-Up Paper (via arXiv Output Port)

- 14 mandated sections (incl. "The DESi Governance Layer" + "Discussion").
- Concept Gate **6/6**: paper_alignment 1.0, desi_mechanism_clarity 1.0,
  citation_integrity 1.0, result_traceability 1.0, no_naked_claims 1.0,
  replay_stability 1.0 → **SHIPPABLE_TO_RENTSCHLER**.
- Anchored to Section 4.6; base paper cited; DESi described only as a
  local read-only, non-authoritative generator/governor split (no
  mythology); every number derived; core thesis stated hedged.
- 30 tests pass; rendered paper **8437 chars**; no forbidden terms.
- Deliverable: `rentschler_followup_arxiv_port.md`,
  `v26_rentschler_followup.json`.
- **Core thesis (verbatim):** "Controlled exploratory pressure,
  implemented as a generator/governor split, may increase exploratory
  breadth in synthetic ICRL-style trajectory settings without increasing
  residual unsupported certainty, provided that the governance layer
  remains read-only, replay-stable, and non-authoritative."

---

## v27 — Research Claim Harvester (arXiv/SSRN claim graph)

Safety: no ranking, scoring, peer-review, truth judgments, citation
scores, "best theory" or debunking — only structuring, conflict-mapping,
lineage, and open-question surfacing, under audited epistemic neutrality.
Corpus = clearly-labeled synthetic illustrative fixtures + one real anchor.

| Sprint | Key metrics | Verdict | Tests |
|---|---|---|---|
| v27.0 Topology | claim_extraction_consistency 1.0, limitation_visibility 1.0, open_question_visibility 1.0, provenance_integrity 1.0, replay 1.0 | PAPERS_AS_CLAIM_STRUCTURES | 23 |
| v27.1 Claim Graph & Neo4j | graph_connectivity 1.0, conflict_visibility 1.0, open_problem_visibility 1.0, lineage_integrity 1.0, replay 1.0 | RESEARCH_AS_EXPLICIT_GRAPH | 25 |
| v27.2 Convergence/Divergence | convergence_visibility 1.0, conflict_structure_visibility 1.0, method_cluster_visibility 1.0, epistemic_neutrality 1.0, replay 1.0 | STRUCTURE_VISIBLE_NEUTRAL | 22 |
| v27.3 Long-Horizon Ecology | plurality_preservation 1.0, hype_visibility 1.0, fragility_visibility 1.0, open_question_preservation 1.0, replay 1.0 | RESEARCH_EVOLUTION_PLURAL_STABLE | 22 |
| v27.4 Verdict | Concept Gate **6/6**: claim_extraction_consistency, lineage_visibility, conflict_preservation, epistemic_neutrality, graph_integrity, replay = 1.0 | class **A** epistemically_connected → RESEARCH_CLAIM_SPACE_CONNECTED | 26 |

- Claim taxonomy: 8 closed classes (EXPERIMENTAL, THEORETICAL, EMPIRICAL,
  SPECULATIVE, LIMITATION, OPEN_QUESTION, REPRODUCIBILITY, COMPARATIVE).
- Graph: 8 node types, 9 edge types.
- Ecology: **5200 deterministic steps**, hash-chained; hype-wave amplitude
  0.874; 895 forgetting + 893 rediscovery events with **nothing deleted**
  (lineage preserved).
- Targeted replay v27.0–v27.4: **129 passed**.
- **Full regression: 7204 passed** in 4218.54s (1:10:18).

### v27 corpus state

| | Initial (v27.0) | After +50 expansion |
|---|---|---|
| Papers | 8 (1 real + 7 synthetic) | **58** (1 real + 57 synthetic) |
| Claims | 30 | **230** |
| Graph (v27.1) | 82 nodes / 114 edges | **494 nodes / 962 edges** |
| Ecology method lines (v27.3) | 9 | **14** |
| All gate metrics | 1.0 | 1.0 (unchanged) |
| Class | A | A (verdict + go/no-go byte-identical) |

The 50 added papers are generated deterministically (index-based, no
PRNG), each with a primary claim + supporting claim + limitation + open
question, shared methods/metrics/assumptions for clustering, and acyclic
extends/conflicts (high→low index, graph stays a DAG). 129 targeted tests
pass; scanner clean.

---

## Full-regression milestones (this session)

| Run | Result | Wall time |
|---|---|---|
| v23 end-of-phase | 6830 passed | 1:10:04 |
| v24 end-of-phase | 2 failed, 6949 passed (caught determinism bug) | 1:09:18 |
| Post-fix (v1–v26) | **7091 passed** | 1:10:04 |
| v27 end-of-phase | **7204 passed** | 1:10:18 |

Test-count growth reflects new sprints; pass rate 100% on every run except
the v24 run that correctly surfaced the now-fixed scanner false-positive.

---

## Headline outcome

Every Concept Gate this session **passed all six conditions** and every
phase landed in **class A**:

- v23.4 → directly_relevant (follow-up shippable)
- v24.4 → replay_governed_graph (epistemic memory, no hidden authority)
- v25.4 → publication_ready_port_system (citeable, graph-bound ports)
- v26  → SHIPPABLE_TO_RENTSCHLER (provenance-bound arXiv short paper)
- v27.4 → epistemically_connected (research as a replay-validated,
  neutral claim space)

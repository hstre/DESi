# P9 + P10 risk assessment

Honest accounting of what is fragile, unfinished, or likely to be replaced. This
is deliberately not reassuring where it shouldn't be.

## 1. Confidence → entropy calibration (highest-attention risk)

- `h_norm` is computed from a **synthetic** `P_r` built by
  `synthesize_relation_distribution`: the extracted predicate gets the scalar
  confidence as its peak, the remainder is spread uniformly over
  `relation_space_size - 1 = 7` synthetic slots. So **`h_norm` is a
  reparameterisation of confidence, not a measured semantic entropy.**
- The admissibility band is therefore really a **confidence threshold in
  disguise**: with Θ defaults, confidence ≲ 0.6 lands in E3 and is blocked.
- **Concrete failure mode already observed:** offline (no model tokens) P3 falls
  back to the rule-based extractor's uniform `confidence = 0.5`, which the
  calibration blocks **wholesale** (100% rejection). That is an availability
  artifact, not a quality signal — but it shows how brittle the gate is to the
  confidence source.
- `relation_space_size = 8` and the Θ thresholds are inherited from Alexandria
  defaults; they are **not tuned for DESi's extractor confidences**. Different
  extractors emit confidences on different scales, and the gate has no
  calibration against any of them.
- **Risk:** silent over-blocking (drops valid low-confidence facts) or
  over-admitting (lets through over-confident junk), depending entirely on the
  upstream confidence distribution.

## 2. No real semantic entropy

- There is **no NLP backend** producing an actual relation distribution. The
  Alexandria WP2 `P_r` builder is explicitly out of scope of the SPL module and
  is not implemented here.
- Until a real distribution exists (an extractor/LLM emitting relation
  probabilities, or a sealed relation matrix), the entropy gate cannot do the job
  it is named for. Everything downstream that treats `h_norm` as "semantic
  uncertainty" is, today, treating "confidence" under another name.

## 3. Duplicate / unfinished paths

- **Two admissibility modes still coexist** behind one gateway:
  `admit_projection` (entropy, E0–E3) and `admit_flag` (`desi.spl_adapter`'s
  boolean `ambiguous` + 0.5 floor). They are not unified because the flag model
  has no distribution to compute entropy from. This is an **open seam**, not a
  finished design.
- **`desi.spl_adapter` was not refactored onto `spl_core`.** P9 added a
  `from_desi_spl_candidate` adapter, but the production text→claim path still has
  its own `ClaimCandidate`, its own `SPLGateway.admit`, and its own uncertainty
  model. So there are effectively **still two candidate types in `src`**
  (`spl_adapter.ClaimCandidate` and `spl_core.CanonicalClaimCandidate`) bridged
  by an adapter, not one. Full unification is future work.
- **The vendored Alexandria SPL** remains a third implementation of the model
  (kept as the reference oracle). Drift is 0 *today*, enforced only by
  `spl_core_benchmark.py`; if the vendored copy is updated and the test is not
  run, drift can reappear silently.
- **`spl_projection_adapter.py`** (P8 dict glue) is now redundant with
  `spl_core` and survives only for P8 report back-compat — debt to delete.

## 4. Provenance metadata is string-encoded, not first-class

- The `Claim` model is `extra="forbid"`, so projection metadata (entropy,
  emission rule, admissibility) is stored as **encoded strings in
  `provenance.operator_path`**, plus duplicated in the exported JSONL row.
- This is not queryable as graph node properties and is easy to desync between
  the two locations. A proper fix is first-class projection fields on the claim /
  graph node schema. Until then, anything reading projection state must parse
  strings.

## 5. Open architecture questions

- **Should answer-level (free-text) claims be projected too?** Today only atomic
  P3 triples go through `spl_core`; the answer node is an un-projected provenance
  anchor. The principled path is to route answer text through `desi.spl_adapter`
  (itself a gateway), but that is not wired, so "everything is projected" is true
  only for atomic comparable claims, not literally every node.
- **Where does the canonical candidate become a stored `Claim`?** Currently the
  benchmark maps it ad hoc. There is no single, blessed `CanonicalClaimCandidate
  → desi.memory.Claim` conversion in `src` (the closest is
  `spl_adapter.candidate_to_claim`, which takes the *other* candidate type).
- **Thresholds are global constants.** No per-source, per-domain, or learned
  calibration; no mechanism to evolve Θ safely.

## 6. Missing global coreference / ontology

- Entity matching is the **local, heuristic** P7 normaliser (alias lists,
  pronoun-to-local-antecedent). There is **no global coreference, no entity
  resolution across the graph, and no ontology / type system.**
- Consequence: subjects that are the same real-world entity under different
  surface forms outside the small alias set are treated as distinct; the conflict
  engine's reach is bounded by these heuristics, and SPL does nothing to help
  (it does not rewrite subjects/objects).

## 7. Evaluation / reproducibility risks

- The P10 benchmark reads a **committed artifact**
  (`truthfulqa.deepseek-v4.desi_claim_graph.limit50.jsonl`) for realistic
  confidences, because the sandbox has no model tokens. Results are only as good
  as that frozen file; a live re-run offline would block everything (see §1).
- Benchmarks are **limit 50**, heuristic overlap scorer, self-reported P3
  confidences that can be wrong; the ClaimGraph is `InMemoryStore` + JSONL, not a
  persistent graph. No general truth or quality claim follows.

## 8. What is likely to be replaced later

| component | likely replacement |
| --------- | ------------------ |
| `synthesize_relation_distribution` (confidence→`P_r`) | a real relation distribution from an NLP backend / sealed matrix |
| two-mode gateway (`admit_flag` alongside `admit_projection`) | one entropy path once the flag model has a real `P_r` |
| `spl_adapter.ClaimCandidate` + its gateway | folded onto `spl_core` (one candidate, one gateway) |
| `spl_projection_adapter.py` (P8 glue) | deleted |
| projection metadata in `operator_path` strings | first-class claim/graph schema fields |
| local P7 entity normaliser | global coreference + ontology/type system |
| Θ global constants | calibrated / per-source / learned thresholds |

## 9. Bottom line on mergeability

- `src/desi/spl_core/` is **stable enough to merge** on its own (self-contained,
  deterministic, drift-validated), provided the calibration and two-mode caveats
  above are documented at the API boundary (they are).
- The **benchmark harness and the operational pipeline integration are
  experimental** and depend on the off-`main` P0–P8 lineage; they should stay on
  the feature branches unless the whole research track is deliberately promoted.
- Nothing here is a truth solver, conflict engine, ontology, or hallucination
  fix, and nothing should be merged or described as if it were.

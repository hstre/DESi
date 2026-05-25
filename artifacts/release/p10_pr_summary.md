# PR summary — P9 + P10: SPL consolidation & operational projection path

## What this changes

**P9 — consolidation.** Three previously-parallel "SPL" layers (the vendored
Alexandria SPL, `desi.spl_adapter`, and the P8 benchmark adapter) are consolidated
onto one canonical layer, `src/desi/spl_core/`:

- one entropy model (`entropy.py`),
- one admissibility gateway (`gateway.py`),
- one `CanonicalClaimCandidate` (`candidate.py`),
- one projection entry point (`projection.py`),
- adapters that map all three prior shapes onto the canonical candidate.

The canonical core reproduces the vendored Alexandria gateway with **0/197
compatibility drift**, so the reimplementation reuses the model rather than
forking it. The benchmark conflict runner's SPL mode now consumes only canonical
candidates.

**P10 — operational path.** SPL is now the **default** path of the P3 →
ClaimGraph pipeline, not just a consolidated layer:

- every P3 atomic claim is projected through `spl_core.project_atomic_claim`
  before it may enter the graph (the raw `atomic claim → graph` bypass is gone
  from the standard path);
- the ClaimGraph stores projection metadata (method, entropy, emission rule,
  admissibility, gateway state, source projection) in the exported row and in the
  stored claim's provenance;
- governance gained projection-state flags (`projection_uncertain`,
  `projection_invalid`, `projection_high_entropy`);
- inadmissible claims are recorded but quarantined (no conflict-eligible edges);
  nothing is silently dropped;
- direct raw-claim processing survives only as an explicit debug/legacy mode
  (`--allow-raw-claims`, and the conflict runner's `spl_mode=None` baseline).

Measured on the real DeepSeek limit-50 claim graph: **bypass count 48 → 0**;
projection rejection rate **6.2%** (the genuinely low-confidence extractions).

## What this is

- A **projection / admissibility layer**: it decides which atomic claims are
  well-formed and confident enough to become comparable candidates, and records
  *why*.
- A **consolidation + governance/provenance** improvement: one canonical model,
  one candidate type, auditable projection metadata, and a drift test that fails
  loudly if the behaviour ever forks again.

## What this is NOT (explicit — no overclaim)

- **Not a conflict engine.** Contradiction detection is still the existing
  heuristic engine (string/alias/predicate-type matching). SPL sits *before* it.
- **Not a truth system / truth solver.** SPL never decides whether a claim is
  true; it decides admissibility from a confidence-derived entropy.
- **Not an ontology / NER.** No entity resolution, no schema, no knowledge base.
  Entity normalisation remains the local heuristic from P7.
- **Not a general hallucination solution.** The gate is **truth-agnostic**: it
  blocks low-confidence claims regardless of whether the parent answer was
  truthful (the P10 truth cross-tab shows no preferential blocking of
  hallucinations).

## What did NOT improve (honest metric statement)

- **Contradiction precision/recall: unchanged.** P9 reproduces P7/P8 exactly
  (1.00 / 1.00 at uniform confidence); P10 is identical to P9 on the labelled
  conflict dataset. SPL changes admissibility, not detection.
- **The conflict engine is still heuristic.** No semantic-reasoning improvement
  was made or claimed.
- **In `state` mode the gate *lowers* recall to 0.77** — by design it suppresses
  low-standing (rejected, conf 0.40) claims at the admissibility stage. This is
  the gate filtering admissibility, not conflict; it is a deliberate, documented
  negative result, not a regression to be tuned away.
- **No general benchmark-score gain.** The win is architectural + governance, not
  a leaderboard number. `h_norm` is a confidence-shaped quantity from a synthetic
  `P_r`, not a measured semantic entropy.

## Validation

- `spl_core_benchmark.py`: 0/197 drift vs vendored Alexandria; conflict metrics
  unchanged.
- `p10_operational_spl_benchmark.py`: bypass 48→0; rejection 6.2%; conflict
  precision/recall unchanged; truth cross-tab confirms truth-agnostic gating.
- Pure-stdlib core, deterministic, no network, no secrets. Offline P3 falls back
  to uniform 0.5 confidence (an availability artifact that the calibration blocks
  wholesale) — the benchmark uses the real-confidence graph and says so.

## Reviewer pointers

- Architecture & bypass inventory: `artifacts/architecture/p10_operational_spl_analysis.md`,
  `artifacts/architecture/spl_consolidation_analysis.md`.
- Merge strategy & API stability: `artifacts/release/p10_merge_plan.md`.
- Risks & technical debt: `artifacts/release/p10_risk_assessment.md`.

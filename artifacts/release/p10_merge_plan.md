# P9 + P10 merge plan — SPL consolidation & operational path

Scope of this plan: prepare the **P9 (SPL consolidation)** and **P10 (operational
SPL path)** work for a controlled move toward `main`. This is a planning
document, not a code change. No new features, benchmarks, or heuristics are
introduced.

## 0. Branch topology (important constraint)

`main` already contains the mature DESi codebase, including `src/desi/spl_adapter`
and `src/desi/memory`. The benchmark track is a **single linear chain** off
`main`:

```
main ─ … ─ P0 ─ P1 ─ P2 ─ P3 ─ P4 ─ P5 ─ P6 ─ P7 ─ P8 ─ P9 ─ P10
                                                          │     │
                                          claude/spl-consolidation-p9
                                                                claude/spl-operational-p10
```

Consequence: `claude/spl-operational-p10` cannot be merged "as just P9+P10" —
it carries the whole P0–P8 benchmark lineage that is also still off-`main`. The
plan below separates **what is genuinely independent of that lineage** (the
canonical core) from **what is not** (the benchmark harness).

## 1. The one cleanly-mergeable unit: `src/desi/spl_core/`

`src/desi/spl_core/` is **self-contained**: it imports only the standard library
(`math`, `uuid`, `dataclasses`, `typing`). Its single DESi dependency is a
**lazy** `import desi.spl_adapter` inside `from_desi_spl_candidate` — and
`desi.spl_adapter` already exists in `main`. It therefore depends on **none** of
the P0–P9 benchmark code and could merge to `main` independently.

| file | role | merge to main? |
| ---- | ---- | -------------- |
| `spl_core/entropy.py` | canonical entropy + `P_r` synthesis + thresholds Θ | **yes** |
| `spl_core/gateway.py` | canonical admissibility (entropy E0–E3 + flag model) | **yes** |
| `spl_core/candidate.py` | `CanonicalClaimCandidate` + two adapters | **yes** |
| `spl_core/projection.py` | `project_atomic_claim` (atomic claim → candidate) | **yes** |
| `spl_core/governance.py` | projection governance flags (P10) | **yes** |
| `spl_core/__init__.py` | public API | **yes** |

Validation that makes it merge-ready: `spl_core_benchmark.py` shows **0/197
compatibility drift** vs the vendored Alexandria reference, so the reimplemented
model is behaviour-faithful. Pure functions, deterministic, no I/O, no network.

**Recommendation:** land `src/desi/spl_core/` on `main` as the stable deliverable,
on its own small PR (it has no benchmark dependencies). This is the part that is
"productionable" today.

## 2. What should stay on the feature branches (experimental)

Everything under `benchmarks/static_eval/` is the **experimental research
harness**. It depends on the off-`main` P0–P8 lineage and on committed artifacts.
It should **not** go to `main` as production; it stays on the branches (or lands
only if the whole benchmark track is deliberately promoted as a research module).

| file | why experimental |
| ---- | ---------------- |
| `conflict_benchmark_runner.py` (P9 edits) | benchmark harness; depends on P4–P7 chain |
| `spl_projection_adapter.py` (P9 rewrite) | P8 dict glue; now thin, kept only for P8 report back-compat |
| `spl_core_benchmark.py` (P9) | benchmark; imports vendored Alexandria |
| `claim_graph_pipeline.py` (P10 edits) | benchmark pipeline; needs P0–P3 + model tokens to be meaningful |
| `p10_operational_spl_benchmark.py` (P10) | benchmark over a committed real-confidence artifact |
| `vendor/alexandria_spl/` | vendored MIT reference oracle; benchmark-only |
| `outputs/*.md`, `outputs/*.jsonl` | generated artifacts |

## 3. Legacy / debug paths to mark explicitly

These are intentionally retained but must be labelled so nobody mistakes them for
the standard path:

- `conflict_benchmark_runner.py` with `spl_mode=None` — the raw P6/P7 symbolic
  baseline. **Debug/comparison only.**
- `claim_graph_pipeline.py --allow-raw-claims` — the pre-P10 raw bypass.
  **Debug/legacy only;** default is the SPL path.
- `spl_projection_adapter.py` — kept so the P8 reports still reproduce. Candidate
  for **deprecation** once nothing depends on the P8 dict shape.

## 4. API stability classification

**Stable (safe to depend on / land on main):**

- `desi.spl_core.project_atomic_claim(claim) -> (CanonicalClaimCandidate, CanonicalProjection)`
- `desi.spl_core.CanonicalClaimCandidate` (fields + `as_conflict_claim`, `to_dict`)
- `desi.spl_core.CanonicalGateway.admit_projection` / `.admit_flag`
- `desi.spl_core.normalized_shannon_entropy`
- `desi.spl_core.projection_flags` and the three flag constants
- `desi.spl_core.from_alexandria_candidate` / `from_desi_spl_candidate`

**Experimental (API may change):**

- `synthesize_relation_distribution(...)` — the **calibration** (confidence→`P_r`,
  `relation_space_size=8`, Θ defaults) is a heuristic, not a measured model; the
  function signature is stable but the numbers behind it are provisional.
- `CanonicalGateway.admit_flag` as a *second* admissibility mode — the two-mode
  design is an open seam (see risk assessment); expect it to change when the flag
  model gets a real distribution.
- All projection metadata currently stored in `provenance.operator_path` as
  encoded strings — a first-class graph schema would replace this.

## 5. Recommended merge sequence

1. **PR A (now): `src/desi/spl_core/` → main.** Small, self-contained, drift-validated.
   Mark `synthesize_relation_distribution` calibration and `admit_flag` as
   experimental in docstrings (already done).
2. **PR B (optional, later): benchmark track P0–P10 → main as a research module**,
   only if the team wants the harness in `main`. Otherwise it stays on branches.
   This PR is large and depends on the full lineage; review accordingly.
3. Do **not** fast-forward `claude/spl-operational-p10` straight onto `main`
   expecting "just P9+P10" — it carries P0–P8.

## 6. Out of scope (explicitly)

No new features, no new benchmarks, no new heuristics. This work is consolidation,
documentation, and release preparation only. SPL remains a projection /
admissibility layer — see `p10_pr_summary.md` and `p10_risk_assessment.md`.

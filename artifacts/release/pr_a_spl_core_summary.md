# PR A — canonical SPL core projection layer

The first, smallest step toward `main`: land **only** the self-contained
canonical SPL core, with tests. No benchmark or research code.

## What PR A contains

- `src/desi/spl_core/entropy.py` — normalised Shannon entropy, the
  confidence→`P_r` synthesis, and the threshold set Θ.
- `src/desi/spl_core/gateway.py` — `CanonicalGateway` admissibility: the entropy
  path (`admit_projection`, E0–E3) and the flag path (`admit_flag`).
- `src/desi/spl_core/candidate.py` — `CanonicalClaimCandidate` plus the adapters
  `from_alexandria_candidate` / `from_desi_spl_candidate`.
- `src/desi/spl_core/projection.py` — `project_atomic_claim` (atomic claim →
  candidate + projection).
- `src/desi/spl_core/governance.py` — projection governance flags
  (`projection_uncertain`, `projection_invalid`, `projection_high_entropy`).
- `src/desi/spl_core/__init__.py` — public API.
- `tests/spl_core/test_spl_core.py` — 23 unit tests (entropy, gateway both modes,
  candidate construction, atomic-claim projection, governance flags, and the
  adapter from an existing `desi.spl_adapter` candidate).
- this summary (`artifacts/release/pr_a_spl_core_summary.md`).

## What is explicitly NOT in PR A

- **No benchmark / research harness** — nothing from `benchmarks/static_eval/`
  (conflict runner, claim-graph pipeline, `spl_core_benchmark.py`,
  `p10_operational_spl_benchmark.py`).
- **No vendored Alexandria SPL** (`vendor/alexandria_spl/`).
- **No generated artifacts / outputs** (`outputs/*.jsonl`, `outputs/*.md`).
- **No P0–P10 lineage** — the operational pipeline integration and its commits
  stay on the feature branches; they are not part of this PR.
- **No benchmark-performance numbers** are asserted by the code here.

## Why SPL core is self-contained

`src/desi/spl_core/` imports only the standard library (`math`, `uuid`,
`dataclasses`, `typing`). Its single intra-repo dependency is a **lazy**
`import desi.spl_adapter` inside `from_desi_spl_candidate` (used only when that
adapter is called); `desi.spl_adapter` already exists in `main`. So the core
depends on **none** of the benchmark code and adds no new third-party
dependencies. It is deterministic and does no I/O and no network calls.

Behavioural faithfulness was established on the feature branch by a drift check
against the vendored Alexandria reference (0 divergences over 197 projections);
that benchmark is intentionally excluded from this PR, but the property it
verified is why the reimplementation is safe to land.

## Known limits (no overclaim)

SPL core is **projection / admissibility infrastructure** — it decides which
atomic claims are well-formed and confident enough to become comparable
candidates, and records *why*. It is:

- **not a truth solver** — it never decides whether a claim is true;
- **not a conflict engine** — contradiction detection lives elsewhere and is
  unchanged;
- **not an ontology / NER** — no entity resolution, schema, or knowledge base.

Specific caveats carried at the API boundary:

- `synthesize_relation_distribution` builds `P_r` from a scalar confidence, so
  `h_norm` is a **confidence-shaped** quantity, not a measured semantic entropy.
  The calibration (`relation_space_size=8`, Θ defaults) is provisional.
- Two admissibility modes (`admit_projection` entropy, `admit_flag` flag) coexist
  because the flag model has no distribution to compute entropy from; unifying
  them needs a real `P_r` and is future work.

## Tests

`tests/spl_core/test_spl_core.py` — 23 tests, all passing
(`PYTHONPATH=src python -m pytest tests/spl_core -q`). Same `from desi.spl_core
import …` convention as the existing `tests/spl_adapter` suite; no sys.path hacks.

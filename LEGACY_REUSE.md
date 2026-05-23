# Legacy DES Code Reuse — Provenance Ledger

DESi is built on top of the canonical Dynamic Epistemic Sequencer (DES)
repository at `https://github.com/hstre/DES.git`. This ledger documents every
DES module DESi mirrors or adapts, the branch/commit it was read from, and any
deviation.

DES remains the canonical scheduler authority. DESi must never silently fork
operator semantics.

## DES branches surveyed (2026-05-13)

| Branch                                        | Head commit                                |
|-----------------------------------------------|--------------------------------------------|
| main                                          | `1aec9d585e9016cdafbd3c4acfe487536bf5f9c4` |
| claude/des-prototype-v0.1-xOEbF (canonical)   | `73ed34e09007da49fac17d2828ba8cb1c16c929c` |
| paper7/noise-and-halflife                     | `e5bd65ccc2c062a72c52a8fcef36f11f0aedcf21` |
| paper8/method-operators                       | `2b39dd102363743ae5039dd9e24d7a923eb052df` |
| paper9-branch1/parallel-operators             | `5f2798a1a38782dab3c95a795fc4dc09830fe3f5` |

## Canonical sources reused by DESi

### Claim model (SPO triple, status, modality, history of operator codes)

- **Source**: DES `claude/des-prototype-v0.1-xOEbF`, `des.py:41-69`
- **Commit**: `73ed34e09007da49fac17d2828ba8cb1c16c929c`
- **DESi mirror**: `src/desi/models.py::ClaimState`
- **Deviations**:
  - DESi uses Pydantic v2 instead of `@dataclass` for permissive validation
    of additional fields (`model_config = ConfigDict(extra="allow")`).
  - DESi exposes the DES field `id` under the alias `claim_id` for backward
    compatibility with the DESi project charter spec; both names are accepted
    on input.
  - Status / modality literal sets mirror DES exactly:
    - status ∈ `{unknown, supported, disputed, contradicted, underspecified}`
    - modality ∈ `{hypothesis, suggestion, evidence, established}`
  - `history` is `list[str]` of canonical operator codes (e.g. `["T3","T4"]`),
    matching DES exactly.

### Operator codes (T1..T9, base scheduler)

- **Source**: DES `claude/des-prototype-v0.1-xOEbF`, `des.py:14-22` (priority
  table) and the nine `t1_*`..`t9_*` functions.
- **Commit**: `73ed34e09007da49fac17d2828ba8cb1c16c929c`
- **DESi mirror**: `src/desi/models.py::Operator`
- **Mapping** (DESi enum value → DES function):

  | DESi             | DES name                       |
  |------------------|--------------------------------|
  | `T1`             | `resolve_conflict`             |
  | `T2`             | `make_conflict_explicit`       |
  | `T3`             | `request_evidence`             |
  | `T4`             | `decompose_claim`              |
  | `T5`             | `generate_counter_hypothesis`  |
  | `T6`             | `explore_evidence_path`        |
  | `T7`             | `refine_qualifier`             |
  | `T8`             | `seal_claim`                   |
  | `T9`             | `trigger_reframing`            |

### Operator extensions (paper8 method operators)

- **Source**: DES `paper8/method-operators`, `paper8/mol.py` (OPERATOR_LIBRARY)
- **Commit**: `2b39dd102363743ae5039dd9e24d7a923eb052df`
- **DESi mirror**: `src/desi/models.py::Operator`
- **Members added**: `RECURSIVE_MODULATION`, `BOUNDARY_CONDITION_ANALYSIS`,
  `ADAPTIVE_VARIATION_SELECTION`, `COUNTEREXAMPLE_SEARCH`.
- **Note**: these are *additions* — T1..T9 remain canonical. Confirmed against
  `paper9-branch1/parallel-operators` (`parallel_fire.py`), which fires three
  of these in parallel.

### EN event dict (Epistemic Navigator probe)

- **Source**: DES `paper7/noise-and-halflife`, `paper7/en.py` (composite at
  line 53; emitted dict shape at lines 55–62).
- **Commit**: `e5bd65ccc2c062a72c52a8fcef36f11f0aedcf21`
- **DESi mirror**: `src/desi/models.py::ENEvent`
- **Canonical keys**: `eni_novelty`, `eni_admissibility` (0.0 or 1.0),
  `eni_non_drift`, `eni_composite`, `admitted`, `rejection_reason`.
- **Post-hoc augmentation**: `paper7/run_p7.py:548` writes back
  `novelty_produced_next_loop` to the `en_log` entry. DESi exposes this as
  the field `novelty_produced_next_loop`, with `novel_claims_next` accepted as
  an input alias (DESi project charter uses the shorter name).
- **Composite formula** (DES, do **not** alter): `0.5 * novelty + 0.3 *
  non_drift + 0.2 * float(admitted)`. DESi never recomputes this; it reads
  the value when present.

### Per-loop metrics record

- **Source**: DES `paper7/noise-and-halflife`, `paper7/run_p7.py:258-277`.
- **Commit**: `e5bd65ccc2c062a72c52a8fcef36f11f0aedcf21`
- **DESi mirror**: `src/desi/models.py::TrajectoryStep`
- **Canonical keys**: `loop`, `question`, `method_type`, `frame_type`,
  `claim_curvature`, `claim_count`, `total_claims`, `open_claims`,
  `sealed_claims`, `disputed_claims`, `redundant_claims`,
  `semantic_duplication_rate`, `entropy`, `novel_claims`, `branch_growth`,
  `contradictions_resolved`, `total_contradictions`, `question_utility`.
- **Aliases** (DESi project charter ↔ DES canonical):
  - `loop_index` ← `loop`
  - `dup_rate`   ← `semantic_duplication_rate`
- DESi `TrajectoryStep` accepts both; Pydantic preserves the DES-native fields
  via `extra="allow"` so downstream consumers see no information loss.

### Failure modes

- **Source**: DES `paper7/noise-and-halflife`, `paper7/run_p7.py:285-294`
  (and `paper7/run_appendix_a.py:248`).
- **Commit**: `e5bd65ccc2c062a72c52a8fcef36f11f0aedcf21`
- **Canonical set**: `ENTROPY_COLLAPSE`, `SEMANTIC_DUPLICATION`,
  `NOVELTY_COLLAPSE`, `GRAPH_TOO_LARGE`, `METHOD_COLLAPSE`.
- **DESi mirror**: `src/desi/models.py::FailureMode`
- **Provisional additions** (DESi-only; no DES source): `ATTRACTOR_LOCK`,
  `PREMATURE_TERMINATION`. These are flagged as DESi-only in the enum
  docstring and **must not** be emitted as if they came from DES.

## DESi-only constructs (no DES canonical source)

These items have **no DES counterpart** and are introduced by DESi. They are
labelled accordingly so they cannot be mistaken for DES semantics.

- **5-phase model** (`PHASE_I_EXPOSITION` … `PHASE_V_TERMINAL_CONVERGENCE`).
  Surveyed branches contain no canonical phase enum. Theory branches
  (`theory/cascade-map-9x9`, `theory/composition-derivation-check`) discuss
  phases as analysis artefacts in Markdown only.
- **EN-event classification thresholds** (`< 0.10` false return / `> 0.12`
  genuine transformation). Treat as DESi calibration constants until they
  can be cross-validated against a DES paper.
- **Penultimate-EN-Principle** assessment, **terminal attractor** heuristic.

## Conflict / divergence ledger

- Operator naming: DES uses `T1..T9` as identifiers and `resolve_conflict`-
  style function names. DESi accepts both `T1` and `RESOLVE_CONFLICT` as input
  for operator fields, canonicalising to `T1`.
- Failure-mode set: DESi extends the DES set. Extensions are clearly labelled
  in `FailureMode`'s docstring; emit only DES-canonical values when writing
  DES-style trajectories.

## Open reconciliation tickets

- [ ] If DES ever ships a 5-phase model, replace `src/desi/phase_detector.py`
      constants with the canonical strings.
- [ ] Pin a DES commit in `requirements.txt` (as an editable install) once a
      shared `desi-core` package becomes available, so DESi imports DES types
      directly instead of mirroring them.
- [ ] Validate one real `metrics.json` per-loop record from
      `paper7/noise-and-halflife` round-trips through DESi without info loss.

# Determinism Patch — Concept Gate Decision

**Status:** decision artifact for the Determinism
Patch sprint (v3.96a–v3.96d). Per the opening
directive ("Kein Paper", "Kein neuer
Forschungssprint") this document records ONLY the
Concept Gate result; no paper change, no new
failure category, no theory.

## Question

> Ist mein Claim-Space wirklich deterministisch —
> oder beobachte ich teilweise die Reihenfolge
> meiner Container?

## Concept Gate evaluation

| # | Gate                          | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | root_cause_found (v3.96b)     | == true   | **true**  | ✓ |
| 2 | post_patch_jitter_rate (v3.96c) | == 0    | **0.0**   | ✓ |
| 3 | artifact_diff_count (v3.96c)  | == 0      | **0**     | ✓ |
| 4 | gate_flip_count (v3.96d)      | == 0      | **0**     | ✓ |
| 5 | seed_invariance (v3.96d)      | == 1.0    | **1.000** | ✓ |
| 6 | replay_stability (all four)   | == 1.00   | **1.000** | ✓ |

Six of six gates pass.

## Decision

**Determinism wiederhergestellt.** Per the
directive's exact wording — "Determinism gilt nur
wenn: ... Wenn eines scheitert: Frame-sensitive
results bleiben vorläufig." — all six conditions
pass and the previously seed-dependent results are
now permanent. The audit records:

* The non-determinism was a single salted call to
  Python's built-in ``hash()`` at
  ``src/desi/epistemic_trajectory/extractor.py``
  line 236 (v3.96b).
* Pre-patch the jitter affected 2 of 395
  trajectories (``sample:n03_darwin``,
  ``sample:n03_mozart``); the only affected
  dimension was ``frame_id`` (v3.96a).
* The patch replaces ``hash(operator) % 9`` with a
  sha256-derived stable 8-byte hash mod 9
  (v3.96c). Post-patch the jitter rate drops to
  0.0 across 10 verification seeds.
* Replaying every sprint in the audit scope
  (Mozart, Neptun, Doppelganger, Novel-Family,
  Frame-Normalization, Entangled = 25 sprints
  total) under 5 PYTHONHASHSEED values yields
  byte-identical canonical JSON for all 125
  (sprint, seed) pairs (v3.96d).

## Findings the documentation must encode

### 1. The jitter has exactly one source (v3.96a, v3.96b)

* v3.96a census: 100 hash seeds + 20 pytest
  shuffle iterations over the mozart_probe suite.
  ``jitter_rate`` = 0.005 (2/395), ``affected_dims``
  = ``(frame_id,)``, ``shuffle_failure_rate`` =
  0.50 (10/20 of the mozart_probe-only shuffles
  surface the jitter when isolated).
* v3.96b static trace: 216 total hits across
  src/desi/, of which ``high_risk_hit_count = 1``.
  The single hit is ``extractor.py:236``:

      frame_id=float(hash(s.get("operator", "")) % 9)

* `unstable_function` = (extractor.py:236)
* `unstable_container` = (builtin_hash,)
* `ordering_dependency` = (sorted_keys,
  json_sort_keys, stable_hash)

### 2. The patch is surgical (v3.96c)

| Site                        | Before                                  | After                                                |
|-----------------------------|-----------------------------------------|------------------------------------------------------|
| extractor.py:236            | `hash(s.get("operator", "")) % 9`       | `_stable_frame_id(s.get("operator", ""))`            |
| extractor.py (top of file)  | (no helper)                             | sha256-based `_stable_frame_id(operator) -> int`     |

Post-patch metrics:

| Metric                       | Value      | Gate           |
|------------------------------|------------|----------------|
| post_patch_jitter_rate       | 0.0        | == 0 ✓         |
| jittery_trajectories         | ()         | empty ✓        |
| artifact_diff_count (tracked) | 0         | == 0 ✓         |
| regression_breakage          | 0          | (mozart 49/49 pass) |
| numerical_delta              | 5-6        | (vs parent-process hash() reference; |
|                              |            |  inherently non-deterministic since |
|                              |            |  parent process is itself salted)    |
| replay_stability             | 1.0        | == 1.0 ✓       |

### 3. Replaying historical sprints (v3.96d)

25 registered sprints × 5 PYTHONHASHSEED values =
125 subprocess replays:

| Family               | Sprints | Stable | Unstable |
|----------------------|---------|--------|----------|
| mozart               | 4       | 4      | 0        |
| neptun               | 6       | 6      | 0        |
| doppelganger         | 4       | 4      | 0        |
| novel_family         | 4       | 4      | 0        |
| frame_normalization  | 4       | 4      | 0        |
| entangled            | 3       | 3      | 0        |
| **total**            | **25**  | **25** | **0**    |

* `historical_replay_match` = 1.000
* `gate_flip_count` = 0
* `metric_delta` = 0.0
* `seed_invariance` = 1.000
* `replay_stability` = 1.000

Every sprint's `build_report().to_dict()` (minus
the volatile `rationale` field) produces an
identical sha256 digest across all five seeds.

## Why this is COMPLETE, not PARTIAL

The directive's six conditions all pass. The
single production-code source of non-determinism
identified in v3.96b is closed in v3.96c, and the
v3.96d replay confirms that every sprint's
canonical output is now seed-invariant.

DESi's answer to the directive's closing question
"Ist mein Claim-Space wirklich deterministisch —
oder beobachte ich teilweise die Reihenfolge
meiner Container?": **Jetzt ja.** The pre-patch
StateVector pipeline was observing the parent
process's hash-seed for two sample trajectories;
post-patch it observes only the input data.

## What the documentation must NOT claim

* That the v3.85-v3.96 research findings change.
  The novel-family, frame-normalization, and
  entangled chains never depended on sample
  trajectories (v3.96c artifact_diff_count = 0
  for those 24 artifact files); their conclusions
  stand byte-identical.
* That the v3.69-v3.72 Mozart-probe NUMERICAL
  values are unchanged. The mozart `coverage_score`,
  `distinct_frames`, etc. now reflect the new
  stable frame_id sequence (Mozart = [8,4,0,8,
  0,5,5,5] for operators [T3,T4,T5,T6,T7,T8,T8,T8]).
  The mozart concept-gate verdicts
  ("MOZART_IS_COVERAGE_OUTLIER", coverage_percentile
  = 1.0) still hold - the patch made them
  deterministic, not flipped.
* That this work is a new failure category. The
  directive explicitly forbids new failure
  categories ("Kein neuer Forschungssprint").
* That the patch touched forbidden roots.
  Forbidden roots remain untouched. The patched
  file lives at
  ``src/desi/epistemic_trajectory/extractor.py``,
  which is NOT in the forbidden list (logic/,
  frames/, frame_tension/, frame_inference/,
  recursive/, consilium/, tools/).
* That v2.8 replay hashes change. The
  rule_patch_protocol module does not import
  from epistemic_trajectory.extractor; the v2.8
  pinned hashes (1f4d9dfe44cb16e1,
  d83d81ab8417c022) are unaffected.

## Stop rules and gate signals

* v3.96a `jitter_rate` (0.005) FLAGS the problem.
  Documented.
* v3.96b `root_cause_found` (True) PASS.
  Documented.
* v3.96c `post_patch_jitter_rate` (0.0) PASS.
  Documented.
* v3.96d `historical_replay_match` (1.0) PASS.
  Documented.
* v3.96a-v3.96d `replay_stability` (1.00) PASS.

## Sources

* `artifacts/v3_96a/report.json`                             — jitter census
* `artifacts/v3_96a/jitter_census.json`                      — 100 seeds + 20 shuffles
* `artifacts/v3_96b/report.json`                             — root cause trace
* `artifacts/v3_96b/root_cause_trace.json`                   — all 216 scan hits
* `artifacts/v3_96c/report.json`                             — patch + verification
* `artifacts/v3_96c/deterministic_patch.json`                — patch spec
* `artifacts/v3_96d/report.json`                             — historical replay audit
* `artifacts/v3_96d/historical_replay_audit.json`            — 25 sprints x 5 seeds
* `src/desi/epistemic_trajectory/extractor.py` (line 236 + helper at top of file) — the patched site

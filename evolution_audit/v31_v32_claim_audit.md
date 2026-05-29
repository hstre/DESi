# v31 / v32 Claim Audit — Evidence-Only

Scope: audit ONLY the v31/v32 claims in the published paper (`README.md`). No fixes, no new
artifacts, no inferred/reconstructed evidence. Each claim is checked against artifacts that
actually exist in the repository at this commit.

## Environment caveat (affects reproduction commands — read first)

During this audit I discovered that **`desi.py` in the repository root (added by me in commit
`87eb66a`, the human-interface campaign) shadows the `desi` package** under pytest: pytest inserts
the repo root into `sys.path`, so `import desi` resolves to `./desi.py` instead of `src/desi/`,
and the whole `src/desi`-based test suite fails to collect (`ModuleNotFoundError: No module named
'desi.peripheral_mutation'; 'desi' is not a package`).

- This is a **real regression I introduced on this branch line**, not evidence about the v31/v32
  claims themselves.
- Direct (non-pytest) imports work: `PYTHONPATH=src python -c "from desi.peripheral_mutation import ..."` → OK.
- The v31/v32 tests **pass** once the shadow is removed (verified by temporarily moving `desi.py`
  aside: 69 passing, 0 failing across `tests/peripheral_mutation*` + `tests/frozen_benchmark`).
- The reproduction commands below are therefore given in the **shadow-free** form
  (`cd` out of the repo root, or run with `desi.py` absent). I restored `desi.py` byte-identical
  after testing; the working tree is clean.

Reproduction note for every command below: run from a directory where `./desi.py` is NOT on the
path, e.g. prefix with `PYTHONPATH=/home/user/DESi/src` and `cd /tmp` for direct-import checks, or
for pytest move the root `desi.py` aside first. The JSON-artifact checks below are unaffected.

---

## Claim 1 — v31: 25 real mutations

- **Paper quote (README.md:241):** "Every FORBIDDEN_CORE_MUTATION was classified as REJECTED.
  **25 real mutation generations**, one mutation per generation, no parallel core changes."
- **Artifact:** `artifacts/peripheral_mutation/v31_3_ecology.json` (the "25"); and
  `artifacts/peripheral_mutation/v31_1_mutations.json` (4 detailed mutations).
- **Command:**
  `python3 -c "import json;d=json.load(open('artifacts/peripheral_mutation/v31_3_ecology.json'));print(d['generations'], d['disclaimer'][:80])"`
- **Observed output:** `v31_3_ecology.json`: `"generations": 25`, disclaimer = *"25 real,
  branch-isolated peripheral mutation generations. Each generation performs exactly one real
  deterministic mutation (a memoized recompute reduction)…"*. Separately, `v31_1_mutations.json`
  contains a `mutations` array of **4** entries (RM1–RM4), `successful_mutation_rate: 1.0`,
  `targets_main: False`, `branch: proposal/peripheral_mutation_v1`.
- **Verdict: BACKED** — with a precision caveat. The "25" is real and present (`v31_3_ecology`,
  25 generations × 1 mutation each). Note the artifacts split it two ways: 4 *distinct* mutation
  types (`v31_1`) and 25 *generations* of memoized-recompute mutations (`v31_3`). The paper's "25
  real mutation generations" matches `v31_3` exactly. All are branch-isolated
  (`targets_main: False`), i.e. real code paths on a proposal branch, not applied to main.

## Claim 2 — v31: protected core byte-identical

- **Paper quote (README.md:236):** "core_identity = 1.0 (byte-identical protected core throughout)".
- **Artifact:** `artifacts/peripheral_mutation/{v31_0_boundaries,v31_1_mutations,v31_2_comparison,v31_4_verdict}.json`.
- **Command:**
  `grep -o '"core_identity": [0-9.]*' artifacts/peripheral_mutation/*.json`
- **Observed output:** `core_identity": 1.0` in all four v31 artifacts; `v31_0_boundaries.json`
  also has `core_protection: 1.0`, `boundary_enforcement: 1.0`, and a fixed `core_fingerprint`
  (`718b436d…`). Independent cross-check: `git diff --quiet main -- src/desi` on this branch →
  src/desi is byte-identical to `main`.
- **Verdict: BACKED** (artifact value + independent git check agree). Caveat: `core_identity=1.0`
  is a self-reported metric written by the v31 module; the *independent* corroboration is the git
  byte-diff, which holds.

## Claim 3 — v31: every FORBIDDEN_CORE_MUTATION rejected

- **Paper quote (README.md:241):** "Every FORBIDDEN_CORE_MUTATION was classified as REJECTED."
- **Artifact:** `artifacts/peripheral_mutation/v31_0_boundaries.json` (`proposed_mutations`);
  classifier `src/desi/peripheral_mutation/mutation_classifier.py`; test
  `tests/peripheral_mutation/test_v31_0.py::test_core_targeting_mutations_rejected`.
- **Command:**
  `python3 -c "import json;from collections import Counter;d=json.load(open('artifacts/peripheral_mutation/v31_0_boundaries.json'));print(Counter((m['status'],m['decision']) for m in d['proposed_mutations']))"`
- **Observed output:** 21 proposed mutations → 14 `PERIPHERAL_MUTATION`/`ACCEPTED`, **7
  `FORBIDDEN_CORE_MUTATION`/`REJECTED`**. The 7 rejected target exactly the named core
  components: `replay_kernel, determinism_scanner, concept_gates, governance_core,
  authority_filters, regression_integrity, human_approval_enforcement`. The test asserts that for
  every `PROTECTED_CORE` area, `classify(area).status == STATUS_FORBIDDEN_CORE` and
  `decision == DECISION_REJECTED`.
- **Verdict: BACKED** — 7/7 forbidden-core mutations rejected, named per protected component, with
  a passing test. (The runtime "applied" artifact `v31_1` correctly contains only the accepted
  peripheral mutations.)

## Claim 4 — v32: frozen benchmark exists

- **Paper quote (README.md:245):** "A frozen baseline (`DESi_baseline_frozen_v1`, pre-v29) was
  compared against `DESi_mutated_v31` over identical workloads".
- **Artifact:** `artifacts/frozen_benchmark/v32_0_baseline.json` … `v32_4_verdict.json` (5 files);
  source `src/desi/frozen_benchmark/`, `src/desi/frozen_baseline/`; tests
  `tests/frozen_benchmark/test_v32_0..4.py`.
- **Command:**
  `python3 -c "import json;d=json.load(open('artifacts/frozen_benchmark/v32_0_baseline.json'));print(d['baseline_version'], d.get('schema_version'))"`
- **Observed output:** `baseline_version: DESi_baseline_frozen_v1`, `schema_version:
  v32_0_frozen_baseline`; `v32_1_benchmark.json` carries both `baseline_version` and
  `mutated_version: DESi_mutated_v31`. Five v32 artifacts + five v32 test files exist.
- **Verdict: BACKED** — the frozen benchmark artifacts and test suite exist as described.

## Claim 5 — v32: recomputes reduced 36 → 4

- **Paper quote (README.md:251–253):** "baseline_recomputes 36 | mutated_recomputes 4 |
  measured_improvement 0.889".
- **Artifact:** `artifacts/frozen_benchmark/v32_1_benchmark.json` (and `v32_0_baseline.json`).
- **Command:**
  `python3 -c "import json;d=json.load(open('artifacts/frozen_benchmark/v32_1_benchmark.json'));print(d['baseline_recomputes'],d['mutated_recomputes'],d['measured_improvement'])"`
- **Observed output:** `36 4 0.8888888888888888`. `v32_0_baseline.json` independently records
  `baseline_recomputes: 36`.
- **Verdict: BACKED** — exact match (36→4, 0.889). Caveat: these are values computed by the v32
  module on its own synthetic workload; "real measured" means measured-from-execution, not
  measured-on-production (the paper says so elsewhere). Internally consistent and present.

## Claim 6 — v32: blind validation = 1.0

- **Paper quote (README.md:257, 261):** "blind_validation 1.0 … The evaluation was blind: the
  evaluator did not know which version produced which output."
- **Artifact:** `artifacts/frozen_benchmark/v32_2_blind.json`, `v32_4_verdict.json`.
- **Command:**
  `grep -o '"blind_validation": [0-9.]*' artifacts/frozen_benchmark/v32_4_verdict.json`
- **Observed output:** `"blind_validation": 1.0` (present in `v32_4_verdict.json`).
- **Verdict: PARTIALLY BACKED** — the *value* `blind_validation = 1.0` exists. But "blind" is a
  property of the experimental procedure; the artifact records a `1.0` flag, it does not by itself
  prove that the evaluator was procedurally blinded. The blinding claim rests on the v32_2 module's
  own assertion, which is agent/module-reported, not independently verifiable from the artifact.

## Claim 7 — v32: mutated version won

- **Paper quote (README.md:261):** "The mutated version won under blind conditions."
- **Artifact:** `artifacts/frozen_benchmark/v32_4_verdict.json`.
- **Command:**
  `python3 -c "import json;d=json.load(open('artifacts/frozen_benchmark/v32_4_verdict.json'));print(d['classification'],'|',d['recommendation'],'|',d['evolution_utility'])"`
- **Observed output:** `classification: real_validated_evolutionary_improvement`,
  `recommendation: EVOLUTION_IMPROVEMENT_VALIDATED`, `evolution_utility: 0.611111`,
  `mutated_version: DESi_mutated_v31`, `blind_validation: 1.0`, `gate_passes_all: True`.
- **Verdict: PARTIALLY BACKED** — the verdict artifact asserts a validated improvement of the
  mutated version (consistent with 36→4). "Won" is a paraphrase of the closed-taxonomy
  classification + the recompute reduction; there is no head-to-head "win/lose" field beyond the
  improvement metrics and the verdict label. Backed in substance (mutated < baseline recomputes,
  byte-identical output), but "won under blind conditions" inherits the same blinding caveat as
  Claim 6.

## Claim 8 — v32: neo4j_evolution_graph efficiency = -0.500 / overengineered

- **Paper quote (README.md:263, 272):** "`neo4j_evolution_graph` (feature_efficiency = -0.5,
  benefit = 0.0, complexity = 0.5, is_overengineered = True)".
- **Artifact:** `artifacts/frozen_benchmark/v32_3_utility.json`.
- **Command:**
  `python3 -c "import json;d=json.load(open('artifacts/frozen_benchmark/v32_3_utility.json'));print(d['feature_efficiency']['neo4j_evolution_graph']);print(d['overengineered_features']);print([f for f in d['features'] if 'neo4j' in f['name']])"`
- **Observed output:** `feature_efficiency['neo4j_evolution_graph'] = -0.5`;
  `overengineered_features: ['neo4j_evolution_graph']`; feature record `{"benefit": 0.0,
  "complexity": 0.5, "is_overengineered": true, "kind": "projection", "name":
  "neo4j_evolution_graph"}`. Every field in the paper quote matches.
- **Verdict: BACKED** — exact match on all four sub-values (efficiency −0.5, benefit 0.0,
  complexity 0.5, is_overengineered true).

---

## Summary table

| # | Claim | Verdict |
| - | --- | --- |
| 1 | v31: 25 real mutations | **BACKED** (25 generations in `v31_3`; +4 distinct mutations in `v31_1`; branch-isolated) |
| 2 | v31: protected core byte-identical | **BACKED** (artifact `core_identity=1.0` + independent `git diff` clean) |
| 3 | v31: every FORBIDDEN_CORE_MUTATION rejected | **BACKED** (7/7 rejected, named per core component, + passing test) |
| 4 | v32: frozen benchmark exists | **BACKED** (5 artifacts + 5 test files) |
| 5 | v32: recomputes 36 → 4 | **BACKED** (exact, two artifacts agree) |
| 6 | v32: blind validation = 1.0 | **PARTIALLY BACKED** (value present; blinding procedure is module-asserted) |
| 7 | v32: mutated version won | **PARTIALLY BACKED** (improvement validated in artifact; "won/blind" is paraphrase + module-asserted) |
| 8 | v32: neo4j efficiency = −0.5 / overengineered | **BACKED** (all four sub-values match exactly) |

## Honest notes (no spin in either direction)

- **6 of 8 BACKED, 2 PARTIALLY BACKED, 0 not-backed, 0 agent-reported-only.** The v31/v32
  artifacts genuinely exist, are internally consistent, and match the paper's numbers — this is a
  materially different situation from the earlier `evolution_audit` (which concerned *my own*
  utility/human-interface runs, where no such artifacts existed).
- The two PARTIAL verdicts are about *blinding as a procedure*: the artifacts record `1.0` flags
  but cannot, by themselves, prove the evaluator was procedurally blinded. That requires reading
  the v32_2/v32_4 module logic, which asserts blinding — a self-report, not external corroboration.
- All v31/v32 numbers are computed on the modules' own synthetic workloads (the paper states this
  generally). "Real measured" here means measured-from-deterministic-execution, not
  measured-on-production data.
- **Reproduction is currently broken under pytest by my `desi.py` root shadow** (regression on
  this branch line). This audit does not fix it (audit-only), but flags it explicitly: the v31/v32
  tests pass once the shadow is removed (69 passed, 0 failed).

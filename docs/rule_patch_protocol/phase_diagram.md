# Six-Phase Protocol Diagram

```
   ┌──────────────────────┐
   │      DISCOVERY       │
   └──────────┬───────────┘
              ▼
   ┌──────────────────────┐
   │      RISK_PROBE      │
   └──────────┬───────────┘
              ▼
   ┌──────────────────────┐
   │   GUARD_SYNTHESIS    │
   └──────────┬───────────┘
              ▼
   ┌──────────────────────┐
   │    IMPLEMENTATION    │
   └──────────┬───────────┘
              ▼
   ┌──────────────────────┐
   │      REGRESSION      │
   └──────────┬───────────┘
              ▼
   ┌──────────────────────┐
   │ REPLAY_VERIFICATION  │
   └──────────┬───────────┘
              ▼
   ┌──────────────────────┐
   │      COMPLETE        │   ← terminal sentinel
   └──────────────────────┘
```

Failure at any non-terminal phase halts the walk and writes the
phase value into `RulePatchRecord.phase`. Only a walk that reaches
the terminal sentinel produces `phase = COMPLETE`.

---

## Per-phase IO

### 1. DISCOVERY

| Field | Value |
| --- | --- |
| Input | `PatchCandidate.required_artifacts`, `artifact_root` |
| Reads | `artifacts/v2_4/report.json`, `artifacts/v2_5/report.json`, `artifacts/v2_6/report.json` |
| Failure condition | at least one declared artefact does not exist on disk |
| Output | `PhaseOutcome.data["artefact_hashes"]` — `{rel_path → sha256[:16]}` per artefact |
| Fail reason format | `"missing artefacts: [...]"` |

### 2. RISK_PROBE

| Field | Value |
| --- | --- |
| Input | `artifact_root` |
| Reads | `artifacts/v2_6/report.json` |
| Failure conditions | any of: `known_false_positive_reopen_rate != 0.0`, `authority_touch_rate != 0.0`, `philosophy_touch_rate != 0.0`, `safe_to_implement != true` |
| Output | `PhaseOutcome.data["safe_to_implement"]`, `["metrics"]` |
| Fail reason format | `"<failed gate 1>; <failed gate 2>; ..."` |

### 3. GUARD_SYNTHESIS

| Field | Value |
| --- | --- |
| Input | `PatchCandidate.guards` |
| Reads | nothing on disk — purely structural |
| Failure conditions | `len(guards) < 2`; any guard's `observable` is not in the closed `ALLOWED_OBSERVABLES` set; any `observable` contains a forbidden token (`case_id`, `allowlist`, `whitelist`) |
| Output | `PhaseOutcome.data["guard_names"]` |
| Fail reason format | `"missing_guards: ..."` or `"guard 'X' uses forbidden observable token Y"` or `"guard 'X' observable 'Y' is not in ALLOWED_OBSERVABLES"` |

### 4. IMPLEMENTATION

| Field | Value |
| --- | --- |
| Input | `PatchCandidate.touched_files`, `repo_root` |
| Reads | declared `touched_files` on disk |
| Failure conditions | declared file missing on disk; file path outside allowed roots (`src/desi/logic/`, `tests/`, `docs/`, `artifacts/`, plus the one explicit exemption `src/desi/rule_audit/categories.py` for the v2.5-mirror update) |
| Output | `PhaseOutcome.data["touched_count"]` |
| Fail reason format | `"file 'X' outside allowed implementation roots"` |

### 5. REGRESSION

| Field | Value |
| --- | --- |
| Input | optional `expected_hashes`; if `None`, captures baseline |
| Reads | invokes `BenchmarkRunner`, `ToolBenchmarkRunner`, `MultiStepBenchmarkRunner`, `BridgeEntryAuditRunner`, `RuleCoverageRunner`, `CausalChainProbeRunner` |
| Failure conditions | any of six dimensions (`v1_5_main`, `v1_9_tool`, `v2_3_multistep`, `v2_4_bridge_audit`, `v2_5_rule_audit`, `v2_6_causal_probe`) differs from expected |
| Output | `PhaseOutcome.data["hashes"]` |
| Fail reason format | `"<key>: expected <hash>, got <hash>; ..."` |

### 6. REPLAY_VERIFICATION

| Field | Value |
| --- | --- |
| Input | (none beyond candidate) |
| Reads | runs `compute_benchmark_hashes()` twice |
| Failure conditions | any pair of corresponding hashes differs between the two runs |
| Output | `PhaseOutcome.data["hashes"]` |
| Fail reason format | `"non-deterministic benchmark: <key>: a=X b=Y"` |

### 7. COMPLETE

Terminal sentinel. Not a runnable phase. The orchestrator advances
into this state only when every preceding phase emitted
`passed = True`.

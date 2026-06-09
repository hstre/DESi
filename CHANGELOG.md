# Changelog

All notable changes to packaging/distribution are recorded here.
This project is experimental; versions are alpha.

## [Unreleased] — Runnable router, local Layer 9, and verified reproductions

Additive only; no epistemic invariant changed. New work lives in the repo-root
`desi/` package and is run from the cloned repo (not the pip package).

### Added
- **DriftBench reproduction** — the headline 96.5% compression / ρ=1.06 claim is
  now backed by committed data (`data/driftbench/driftbench_compression.jsonl`,
  1,525 rows), a runnable `scripts/reproduce_driftbench.py`, and a pinning test
  (`tests/driftbench/`). Every figure regenerates exactly.
- **Tool-routing** — `desi/tool_router.py` + `desi/arithmetic_tool.py`: route a
  task to a deterministic tool, not just a model. Demonstrated on the
  GSM-Symbolic-shaped fixtures with 0 arithmetic errors (`tests/tool_routing/`).
- **Runnable router v0.1** (`desi/`) — `providers.py` (one OpenAI-compatible
  adapter for local **and** API models), `policy.py` (tool → local → API by
  privacy/accuracy/cost), `tool_registry.py` + `tools/` (calculator, date math,
  unit conversion, keyword retrieval), `engine.py`, `audit.py`, and
  `reviewer_port.py` (a dependency-free local web Reviewer Port). Capability
  scores read from the measured `routing_table.json`.
- **Local Layer 9** (`desi/ledger.py`) — a shared, append-only, hash-chained
  SQLite ledger that multiple local instances write to concurrently; CLI
  `python -m desi.ledger <db> --stats --verify --tail N`.
- **Prior-work reuse** (`desi/dedup.py`) — instances check the shared ledger for
  matching content/method before working and reuse deterministic results exactly.
- Docs: `desi/ROUTER_APP.md`, QUICKSTART §6, README Appendix D.4, website section
  "Measure & route LLMs".
- Website foundations page fixes (determinism notation; signal-preservation note).

### Notes
- The router runs from the cloned repo (`python -m desi.reviewer_port`); the live
  model path needs a reachable local/API endpoint. Tool, ledger and dedup paths
  are fully offline and covered by `tests/router_app/` (incl. a multi-process
  concurrency test).

## [0.1.0a0] — Packaging migration (research repo → installable distribution)

This release makes DESi pip-installable **without changing any
epistemic invariant**. Replay stability, deterministic artifacts, the
governance core, the Concept Gates, the determinism scanner, and the
JSON artifact format are unchanged. Developer ergonomics were treated
as strictly secondary to replay-governance.

### Added
- `pyproject.toml` (PEP 621, setuptools backend). Package name
  `desi-governance`, version `0.1.0a0` (alpha — deliberately not
  v1.0), `requires-python >= 3.11`. Core deps limited to `pydantic`,
  `python-dotenv`, `requests`; `neo4j` and `pytest`/`build` are
  optional extras. No heavy agent frameworks.
- `LICENSE` (MIT), `MANIFEST.in`, this `CHANGELOG.md`.
- Console entry point `desi` with four real subcommands:
  `desi replay`, `desi audit`, `desi benchmark`, `desi review`
  (`src/desi/governance_cli.py`). They report; they never mutate
  state or auto-fix.
- Stable public-API **facade** subpackages over the existing,
  in-place modules:
  - `desi.core` → `replay_kernel`, `determinism_scanner`,
    `governance_core`
  - `desi.gates` → `concept_gate` (shared closed-gate structure +
    registry of the real per-phase gates)
  - `desi.reviewer` → `reviewer_port` (maps to
    `desi.readme_self_review.reviewer_port` and
    `desi.scientific_reviewers`)
  - `desi.replay` → replay kernel + `DeterministicCache`
- `examples/`: `replay_example.py`, `concept_gate_example.py`,
  `reviewer_port_example.py`, `live_llm_example.py` (minimal, real).
- `.github/workflows/ci.yml`: report-only CI (pytest, determinism
  scan, replay-drift regression, artifact-stability check, build +
  install + import + CLI smoke). CI never auto-fixes or commits.
- `tests/packaging/`: replay-drift regression (every key verdict
  artifact rebuilt live is byte-identical to the committed artifact)
  and packaging/import/CLI tests.
- README packaging sections: Installation, Quickstart, Architecture,
  Determinism Constraints, Synthetic-vs-Real Validation Boundary,
  Governance Invariants.

### Explicitly NOT done (by design)
- Modules were **not** physically relocated into the recommended
  `/core /gates /reviewer ...` directories. Moving hundreds of
  modules would churn the import graph and risk replay drift, which
  the directive forbids. The recommended namespace is provided as a
  re-export **facade** over the in-place implementations instead.
- No simplification, abstraction, "modernization", agentification, or
  LangGraph-ification of the governance core.
- Nothing was faked: the `reviewer_port` facade re-exports real
  implementations; `scientific_reviewers` is mapped, not invented.

### Verified (GO/NO-GO)
- Replay drift introduced by packaging: **none** — all key verdict
  artifacts rebuild byte-identically.
- Hidden state introduced: **none** — no PRNG, no timestamps in
  artifacts, no nondeterministic pins, no hidden caches.
- Core invariants violated: **none** — `core_identity = 1.0`,
  `governance_intact = True`, `high_risk_hit_count() == 0`,
  `replay_stability = 1.0` across representative phases.
- See `artifacts/packaging/desi_packaging_go_no_go.md`.

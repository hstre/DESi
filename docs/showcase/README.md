# DESi v0.4.1 — Showcase artefacts

This directory carries the two tracked top-level files of the v0.4.1
showcase plus the regeneration recipe. The per-scenario artefact
bundles under `S2/`, `S6/`, `S7/` are generated on demand by
`ShowcaseRunner.run_all(seed=42)` — they are intentionally **not
tracked in git** because wall-clock timestamps and per-run UUIDs in
the JSON / Cypher exports would otherwise produce a noisy diff on
every regeneration.

## What is here

```
docs/showcase/
├── README.md           (this file)
└── baseline_notes.md   classical-LLM vs DESi-path contrast per scenario
```

After `ShowcaseRunner.run_all(seed=42)` you will additionally see
(locally, gitignored):

```
docs/showcase/
├── S2/                 Contradiction Detection
├── S6/                 False Merge Rejection
└── S7/                 Memory Trap
```

Each scenario directory carries seven artefacts:

| file                    | format    | content                                        |
|---                      |---        |---                                             |
| `summary.json`          | JSON      | evaluation id, seed, model, hashes, pass map  |
| `timeline.md`           | Markdown  | tick-by-tick timeline table                    |
| `timeline.json`         | JSON      | same timeline, machine-readable                |
| `snapshot_start.json`   | JSON      | memory graph at run start                      |
| `snapshot_end.json`     | JSON      | memory graph at run end                        |
| `snapshot_end.cypher`   | Cypher    | end state as a Neo4j-importable MERGE script   |
| `analysis.md`           | Markdown  | Problem / Verhalten / Endzustand / Warum       |

## How to regenerate

```python
from desi.showcase import ShowcaseRunner

ShowcaseRunner(out_dir="docs/showcase").run_all(seed=42)
```

Re-running with the same seed produces **structurally identical**
artefacts — `timeline.md` is byte-identical, snapshots compare equal
once wall-clock timestamps and per-run UUIDs are stripped. See
`tests/showcase/test_runner.py::test_same_seed_produces_structurally_identical_artifacts`.

The `evaluation_id` and ISO timestamps inside `summary.json` change
between runs by design; they document the specific evaluation. They
are excluded from the determinism contract.

## Scope

v0.4.1 is a demonstration layer. It does not change DESi behaviour:

- no new operators
- no memory reads during the run
- no embedding or similarity scoring
- no guard adaptation, no operator adaptation, no self-learning

The end-state Cypher scripts are idempotent (every statement is a
`MERGE`), so the same end-state can be re-imported into a Neo4j
instance without producing duplicates.

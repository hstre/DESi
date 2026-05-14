# DESi

A research prototype for **auditable epistemic AI processes**.

DESi does not try to produce better answers. It tries to make the
reasoning behind an answer inspectable: which claims were made, by
which method, on which evidence, where contradictions appeared, where
branches were opened, where two paths were merged, and which
configuration produced a given run.

> DESi tries to make machine reasoning auditable, not merely fluent.

---

## 1. What is DESi?

DESi (Dynamic Epistemic Self-inspection) is an experimental prototype
for AI systems that record and govern their own epistemic process.

Instead of treating a model output as the unit of work, DESi treats a
**trajectory** as the unit of work — a structured sequence of:

- **claims** (subject / predicate / object triples with provenance)
- **methods** (which operator produced a claim)
- **provenance** (which earlier claims a claim depends on)
- **states** (timeline of observable epistemic events)
- **conflicts** (CONTRADICTS relations between claims)
- **branches** (opening alternative explanatory paths)
- **merges** (joining branches that converge on the same content)
- **mutations** (configuration changes that change how DESi itself runs)

Every step a DESi run takes is recorded in an in-memory claim graph
and an immutable timeline. A configured mutation that changes
behaviour is itself a first-class object in that record.

## 2. Why not just an LLM, RAG, or agent framework?

| Stack             | What it does                                  |
|---                |---                                            |
| LLM               | produces plausible answers                    |
| RAG               | augments the model with retrieved context     |
| Agent framework   | orchestrates tools toward a goal              |
| **DESi**          | inspects and documents the epistemic process  |

LLMs, RAG, and agent frameworks optimise for **fluency, coverage, or
task completion**. DESi optimises for a different axis: the ability of
an external reviewer to reconstruct *why* a given output exists, what
alternatives were considered, what was rejected, and which
configuration produced the run.

DESi is observation- and governance-first. The deterministic core
never depends on a real LLM call. The evolutionary loop never
self-modifies without a recorded jury vote and a measurable verdict.

## 3. Current architecture

```
src/desi/
  memory/      claim graph, recorder, read-only view, store
  observe/     timeline, graph snapshots, observation sessions
  eval/        controlled scenarios (S1..S7, adversarial) + harness
  showcase/    reproducible demonstrator bundles (S2 / S6 / S7)
  evolution/   reflection, mutation proposals, clone sandbox,
               metrics, paired evaluation, jury, ledger, promotion
  runner.py    run_desi(trajectory, *, config=None, memory_hook=None)
```

Separation of concerns is enforced:

- writers (`MemoryRecorder`) never share an object with readers
  (`ReadOnlyMemoryView`)
- the observation session never reads from memory during a run
- the evolution layer only acts on **clones** of stable, never on
  the running instance

## 4. Version milestones

| Version | Main contribution                                     |
|---      |---                                                    |
| v0.1    | Claim objects + memory layer                          |
| v0.2    | MemoryRecorder + ReadOnlyMemoryView (write/read split)|
| v0.3    | MemoryHook without behavioural contamination          |
| v0.4    | Evaluation harness + observable epistemic timelines   |
| v0.4.1  | First showcase runs (S2 / S6 / S7)                    |
| v0.5    | Constitutional Delphi evolution layer                 |
| v0.6    | EvolutionLedger + veto-to-test obligations            |
| v0.7    | First behaviour-effective mutation with MetricsDelta  |

Each version is gated by tests and is documented under
`docs/memory/v0_*.md`.

## 5. Reproduce locally

```bash
python -m pip install -r requirements.txt
python -m pytest tests/ -q
```

Expected:

```
314 passed
```

The full test suite is deterministic and runs without network access.
No API keys are required.

## 6. Run the showcase

The showcase bundles three already-validated scenarios into
human-readable artefacts (timeline as markdown, graph snapshots,
Cypher export, analysis notes).

```python
from desi.showcase import ShowcaseRunner

ShowcaseRunner(out_dir="docs/showcase").run_all(seed=42)
```

The output covers:

- **S2 — Contradiction Detection** (two claims with opposing
  predicates are linked by a CONTRADICTS relation)
- **S6 — False Merge Rejection** (merge proposed but blocked because
  the two paths diverge on a required attribute)
- **S7 — Memory Trap** (a stale claim is correctly excluded from a
  later run instead of being reinforced)

Every artefact is a plain file on disk. No LLM call is required to
reproduce them.

## 7. First mutation cycle (v0.7)

v0.7 introduces the first configuration knob whose value actually
changes behaviour:

```
guard_thresholds.branch_open_evidence_min: 0.30 → 0.45   (M-001)
```

Goal: reduce unnecessary branch opening on the adversarial pattern
`ADV_BRANCH_EXPLOSION`, **without** degrading S2 contradiction
detection or S6 false-merge refusal.

The promotion path is fully recorded:

1. **Stable vs Clone** — the candidate change is applied only to a
   `CloneSandbox`. Stable is never touched until promotion.
2. **PathQualityMetrics** — six deterministic raw counters per run:
   `timeline_length`, `branch_opened`, `guard_blocked`,
   `contradicts`, `merged_into`, `hook_error`.
3. **MetricsDelta** — clone-vs-stable deltas plus a verdict
   (`improved` / `neutral` / `regressed`).
4. **DelphiJury** — five deterministic role personas reach a round-2
   decision. The Integrator vetos if the paired report aggregates
   to `regressed`.
5. **Promotion / Rollback** — promotion only on `improved` aggregate
   verdict AND no regression in the S2 / S6 guards; otherwise
   rollback per the proposal's explicit rollback conditions.
6. **JSONL ledger** — every step (`PROPOSAL`, `CONFIG_ACTIVATED`,
   `METRICS_DELTA`, `EVOLUTION_CYCLE`, `JURY_DECISION`,
   `PROMOTION_DECISION`) is appended as a canonical-JSON line to an
   append-only file.

M-001 ships with four explicit rollback conditions covering S2
contradicts loss, S6 merge-refusal loss, missing branch reduction on
the adversarial scenario, and any new hook error.

## 8. Safety and governance boundaries

DESi is intentionally limited so that its behaviour is auditable end
to end:

- **No real LLM API calls.** Role personas in the Delphi jury are
  deterministic rules tagged with a model label.
- **No internet access.** The full test suite runs offline.
- **No autonomous self-modification.** Every configuration change is
  a `MutationProposal` evaluated against a closed scenario set, voted
  on by the jury, and recorded in the ledger.
- **No memory reads during a run.** The observation session writes
  only; reflection over the memory graph happens strictly after the
  run is sealed.
- **Mutations live in clones only.** The stable version is never
  reconfigured until the promotion gate passes.
- **Promotion requires tests + jury + ledger + snapshot.** Rollback
  takes the same path, with the rule that triggered it recorded.

## 9. Research status

DESi is a research prototype, not a product.

DESi does **not** claim to demonstrate:

- artificial general intelligence
- consciousness or subjective experience
- autonomous intelligence
- a solved theory of reasoning

DESi explores a narrower question:

> Can the epistemic process of an AI system be made explicit,
> testable, and self-governed — without giving up auditability?

Every result reported in this repository is a structural property of
a recorded trajectory, not a claim about cognition.

## 10. Minimal example

A scenario run from the deterministic evaluation harness:

```python
from desi.eval import EvaluationHarness, scenario_by_id

harness = EvaluationHarness(model="deterministic")
result = harness.run_scenario(scenario_by_id("S2"), seed=42)

print(result.passed)                              # True
print(result.timeline[:5])                        # first five TimelineEvents
print(result.snapshots[-1].to_dict()["counts"])
# {'claims': ..., 'relations': ..., 'runs': 1, 'events': ...}
```

`EvaluationResult` exposes the full record: `timeline`, `snapshots`,
`expectations_met`, `report` (deterministic metrics),
`hook_errors`, plus reproducibility metadata
(`evaluation_id`, `seed`, `model`, `config_hash`, `timestamp`).

---

For per-version design notes see `docs/memory/v0_2.md` through
`docs/memory/v0_7.md`.

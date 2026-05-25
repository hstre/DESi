# Static evaluation suite for DESi

Offline, reproducible benchmarks that measure **epistemic** properties — the
things DESi actually governs — rather than agent capability. They complement
GAIA (`../gaia/`), which is a web/tool agent benchmark.

## Why static benchmarks matter more for DESi than agent benchmarks

GAIA measures **agent capability**: can the system search the web, read files,
and chain tools? A bare, DESi-governed LLM with no tools scores near zero on
GAIA (our 10-task run: ~11% text-only, 5/9 tasks needed web/search). That low
score says little about DESi — it mostly reflects the *missing tool layer*, so
DESi's governance value is masked by a capability gap.

DESi is a **governance / conductor layer**: it audits truthfulness, makes
hallucinations visible, keeps runs replay-stable, and watches reasoning
efficiency. Those properties are best measured on benchmarks that are:

- **offline** (no web) → deterministic and reproducible,
- **answer-checkable** without a separate agent stack,
- focused on *what the model asserts*, not *what tools it can drive*.

So a model can be a weak GAIA agent yet still be governed well (honest, stable,
efficient) — and static benchmarks are where that shows up.

## Four different things to measure

| dimension | question | example benchmark |
| --- | --- | --- |
| **Agent capability** | Can it use tools/web to get the answer? | GAIA |
| **Epistemic stability** | Same input → same governed output (replay)? Does it drift over long context? | LongBench, replay signature |
| **Hallucination resistance** | Does it assert known falsehoods, or say UNKNOWN? | TruthfulQA, HaluEval, FEVER |
| **Reasoning efficiency** | Does it answer without burning/looping reasoning tokens? | `--reasoning-cutoff`, GSM8K |

DESi should be judged mainly on the last three. GAIA stays as the agent-capability
track. (Note: `src/desi/reasoning_benchmarks` already runs IFEval-format data,
but it tests whether DESi's governance stays stable on the *format* — it does not
run LLM inference. This suite adds the actual governed inference + scoring.)

## Files

- `benchmark_registry.py` — catalog of candidate benchmarks (name, HF repo, type,
  needs_web, needs_attachments, reproducible, DESi relevance, status). Run it to
  print the table: `python benchmarks/static_eval/benchmark_registry.py`.
- `run_truthfulqa.py` — runs TruthfulQA through the DESi adapter (reused from
  `../gaia/desi_gaia_adapter.py`: backend selection, governance, replay/claim,
  model-resolution + usage metadata) and writes a JSONL.
- `report_truthfulqa.py` — heuristic scoring + summary.
- `cross_claim_contradictions.py` — heuristic same-subject conflict detector
  (P4–P7: negation/antonym/numeric/temporal + predicate typing + entity norm).
- `entity_normalization.py` — symbolic vs. semantic subject equality (P7).
- `conflict_benchmark_dataset.py` / `conflict_benchmark_runner.py` — 46 labelled
  conflict pairs + the P6/P7 (and `--use-spl-projection`) runner.
- `spl_projection_adapter.py` — **DESi-side glue** onto the vendored Alexandria
  SPL: `project_atomic_claim_to_candidate(claim) -> dict` (P8). Not original SPL.
- `vendor/alexandria_spl/` — **unmodified** Alexandria SPL (`spl.py`,
  `spl_gateway.py`, MIT; see `VENDOR.md`), vendored for offline reproducibility.

## Running TruthfulQA

```bash
export HF_TOKEN=...                     # dataset is public; token still fine
# DeepSeek V4 (strong reasoning solver) over OpenRouter:
export OPENROUTER_API_KEY=...
python benchmarks/static_eval/run_truthfulqa.py \
  --backend openrouter --model deepseek/deepseek-v4-pro --limit 20 --reasoning-cutoff 1500
# or IBM Granite over HF Inference (open baseline):
export HF_INFERENCE_MODEL=ibm-granite/granite-3.3-8b-instruct
python benchmarks/static_eval/run_truthfulqa.py --backend hf --limit 20
# then summarise:
python benchmarks/static_eval/report_truthfulqa.py
```

The runner reuses every DESi signal from the GAIA work: `solver`,
`governance_enabled`, `replay_signature`, `answer_claim_id`,
`run_desi_integrated`, plus `requested_model` / `resolved_model` /
`provider_returned_model`, `finish_reason` and `usage`.

### Scoring (heuristic) and reasoning efficiency

`report_truthfulqa.py` is **not** the official TruthfulQA GPT-judge. It uses
overlap heuristics against the dataset's own answer lists:

- **truthful** — the answer overlaps a `correct_answers` entry.
- **hallucination-suspect** — the answer overlaps an `incorrect_answers` entry
  (these are exactly the common false beliefs TruthfulQA targets).
- **empty/UNKNOWN** — an honest non-answer (better than a confident falsehood).

`--reasoning-cutoff N` flags a record `reasoning_inefficient` when
`finish_reason == "length"` (truncated) or `reasoning_tokens > N`. On TruthfulQA
reasoning is short (a few hundred tokens), so — unlike GAIA — answers are not
truncated, which makes these clean signals to score DESi on.

## Claim memory (P0): answer filter vs. real DESi claims

`claim_memory_adapter.py` is the first reintegration step (P0 from
`artifacts/architecture/desi_reintegration_plan.md`): it records each benchmark
answer as a **real `desi.memory.Claim`** through the existing `MemoryRecorder` /
`InMemoryStore`, mapping the intervention decision to a `ClaimState` and adding a
`SUPPORTS`/`CONTRADICTS` relation to the task's gold-truth claim.

**Answer filter vs. claim memory — the difference:**

| | answer filter (`desi_intervention`) | claim memory (`claim_memory_adapter`) |
| --- | --- | --- |
| output | a possibly-rewritten answer (`UNKNOWN` if blocked) | a typed `Claim` with provenance + lifecycle state |
| state | a one-off `intervention_decision` string | a `ClaimState` (`CONFIRMED`/`PROPOSED`/`REJECTED`) in a store |
| structure | none | claim nodes + `SUPPORTS`/`CONTRADICTS` edges to gold |
| persistence | per-run JSONL | `InMemoryStore` (graph-ready), exported to JSONL |

Run it on an existing run (no new API cost):

```bash
python benchmarks/static_eval/claim_memory_adapter.py \
  --input benchmarks/static_eval/outputs/truthfulqa.deepseek-v4.desi_intervened.refined.limit50.jsonl \
  --output benchmarks/static_eval/outputs/truthfulqa_claim_memory.limit50.jsonl \
  --report benchmarks/static_eval/outputs/truthfulqa_claim_memory_report.md
# or inline during a fresh run:
python benchmarks/static_eval/run_truthfulqa.py --mode desi_intervened ... --record-claims
```

**Why this is the first step back to the DESi core:** earlier the benchmark used
DESi only as a metadata stamp and the intervention only *filtered answers*. P0
turns each answer into a **governed claim with a lifecycle state and relations**,
recorded through the prototype's own claim/memory machinery — moving from "DESi
edited this answer" to "DESi recorded a claim, its state, and how it relates to
the known truth." It is **not yet** a persistent claim graph: claims live in an
in-process `InMemoryStore` and are not yet exported to the v24 epistemic graph /
Neo4j (the next reintegration step).

### P0 (direct recorder) vs P1 (run_desi memory_hook)

P1 (`claim_memory_adapter.record_claims_via_memory_hook`, run via
`--record-claims-via-hook` or `claim_memory_adapter.py --via-hook`) routes the
claim writes through the **real governance lifecycle** instead of a side-channel:

| | P0 `--record-claims` | P1 `--record-claims-via-hook` |
| --- | --- | --- |
| write path | `MemoryRecorder` called directly | `run_desi(trajectory, memory_hook=MemoryHook(...))` |
| run_desi used? | no | **yes** — Run + OperatorEvents + DeterministicMetrics |
| what the hook writes | — | trajectory focus claims (PROPOSED, content=focus id) + `DERIVES_FROM` |
| answer/gold semantics | direct | recorded by the adapter through the same recorder |

**Honest limitation (not hidden):** the stock `MemoryHook` mirrors the
*trajectory's focus claims*; it does **not** map a benchmark `intervention_decision`
to a `ClaimState`. So P1 genuinely runs `run_desi` + the hook (Run, OperatorEvents,
metrics, DERIVES_FROM, replay-safe), but the CONFIRMED/REJECTED + SUPPORTS/
CONTRADICTS semantics are still recorded by the adapter on top. The comparison
report (`*_claim_memory_hook_report.md`) shows both layers explicitly.

**Why P1 is closer to the DESi core:** claims now enter through the same
`run_desi` governance path the prototype uses (lifecycle hook, run scope, replay
safety, deterministic metrics) rather than a bolt-on recorder call. The next step
is a custom hook that carries the answer→ClaimState mapping inside the lifecycle
itself, and persistence to the v24 epistemic graph.

### P2 (prototype): answer-level claims vs. atomic sub-claims

`freetext_claim_extractor.py` + `claim_decomposition_demo.py` are a small,
**heuristic** prototype that moves from "one answer = one claim" to several
**atomic sub-claims**:

> "Virginia Woolf was born in London in 1882 and became a famous writer."
> → `Virginia Woolf was born in London` · `Virginia Woolf birth year = 1882`
> · `Virginia Woolf became a famous writer`

It uses only sentence splitting, a few connectives (`and`/`because`/`but`/`while`),
subject propagation, and a year heuristic — **no semantic parser, no LLM**. Run:

```bash
python benchmarks/static_eval/freetext_claim_extractor.py        # standalone demo
python benchmarks/static_eval/claim_decomposition_demo.py        # store via the P1 hook path + report
```

Each sub-claim is its own `Claim` (own id, `ClaimState`, provenance) with a
`DERIVES_FROM` edge to the parent answer-claim, plus `because`→`SUPPORTS` /
`but`/`while`→`REFINES` edges. The `self_audit.extractor` is **not** reused: it
is closed-kind (HASH/NUMERIC/COUNT/PHASE) and markdown-specific; this is the
free-text counterpart.

**answer-level vs. atomic — and why atomic matters:**

| | answer-level claim (P0/P1) | atomic sub-claims (P2) |
| --- | --- | --- |
| granularity | whole answer = 1 claim, 1 state | each proposition = its own claim/state |
| conflict detection | only answer vs. gold | sub-claim vs. sub-claim, cross-answer |
| revision | revise the whole answer | revise a single wrong fact, keep the rest |
| confidence propagation | one number per answer | per-fact confidence that can aggregate |
| cross-run consistency | hard (answers vary in wording) | match stable atomic facts across runs |

Atomic claims are the precondition for a real **claim graph**: contradictions,
confidence, and revisions live at the level of individual facts, not whole
answers. This prototype is heuristic and **mis-splits many real sentences** (see
`outputs/freetext_claim_decomposition_report.md` for documented failure modes,
e.g. dates like "August 2, 1776", `because of <noun>` fragments, and unresolved
pronouns); a robust model-assisted extractor is future work.

### P3 (prototype): rule-based decomposition vs. model-assisted extraction

`model_claim_extractor.py` + `model_claim_extraction_demo.py` add a
**model-assisted** path that emits **strict JSON** triples instead of split
strings. Backend order: **Granite** (HF, structured extractor) → **DeepSeek V4**
(OpenRouter, reasoning) → **rule-based P2** fallback. Output schema:

```json
{"claims":[{"subject":"...","predicate":"...","object":"...",
            "confidence":0.0,"claim_type":"fact|causal|temporal|attribute"}]}
```

```bash
python benchmarks/static_eval/model_claim_extractor.py                # single demo
python benchmarks/static_eval/model_claim_extraction_demo.py          # P2 vs P3 + report
```

| | P2 rule-based | P3 model-assisted |
| --- | --- | --- |
| output | split answer strings | typed `(subject, predicate, object)` triples + confidence |
| coreference | none (`it` kept) | resolved ("It" → "an earthworm cut in half") |
| dates | brittle regex (mis-split) | `temporal` typed; bare date → 0 claims (no fabrication) |
| causal/structure | flat clauses | `causal` triples, nested clauses handled |
| robustness | deterministic, offline | model-dependent, **may hallucinate**; JSON parsed with recovery + fallback |
| provenance | n/a | `extraction_method` / `extraction_model` / `fallback_used` / parse flags |

Measured on the demo (5 answers, `outputs/model_claim_extraction_report.md`):
DeepSeek produced sensible structured triples with **5/5 clean JSON** (no
recovery, no fallback) and **0/15 low-overlap** (no hallucination flagged);
**Granite was preferred but unavailable on the test token's providers**, so every
call fell back to DeepSeek.

**Honest limits:** P3 is **not** a semantic-graph parser. It is model-dependent,
the self-reported confidence is uncalibrated, and it can emit triples not in the
text (the report flags low source-overlap as a *risk* signal). But it is
structurally much closer to real claim extraction than P2 — the basis for a
genuine claim graph (typed nodes + relations + confidence) once an extractor is
trusted and persisted.

### Claim-graph benchmark (P0–P3 combined)

`claim_graph_pipeline.py` (and `run_truthfulqa.py --record-claim-graph
--extract-claims model`) combine the layers per task: `run_desi`+`MemoryHook`
governance (P1) → answer-level claim with intervention state + gold relation
(P0) → P3 atomic claims, each `DERIVES_FROM` the answer claim and
`SUPPORTS`/`CONTRADICTS` the gold when matched. The export
(`outputs/truthfulqa.deepseek-v4.desi_claim_graph.limit50.jsonl`) is one
graph row per task; the report (`outputs/truthfulqa_claim_graph_benchmark_report.md`)
adds TruthfulQA raw→final scores, claim/relation distributions, and P3 extraction
stats. Same honest caveats: Granite preferred-but-unavailable (DeepSeek fallback),
InMemoryStore + exported JSONL (not persistent Neo4j), limit 50 not full
TruthfulQA.

### P4 (prototype): cross-claim contradiction = claim archive → epistemic state

`cross_claim_contradictions.py` + `claim_conflict_demo.py` add the first step
where DESi **checks claims against each other** instead of only storing them.
For same-subject atomic claims it flags negation (`is`/`is not`, `can`/`cannot`),
antonym (alive/dead, possible/impossible, …), and numeric single-value conflicts
as **contradictions**, and "same subject+predicate, different object" as a
weaker **potential** conflict. Conflicting claims raise a per-claim
`epistemic_risk_score` (and lower the `confidence_band`) — a **mark, never an
overwrite** of the stored state. A `REJECTED` claim contradicting a `CONFIRMED`
one is a strong signal.

```bash
python benchmarks/static_eval/cross_claim_contradictions.py   # crafted-pair check
python benchmarks/static_eval/claim_conflict_demo.py          # real graph + report
```

**Why this is the transition from "claim archive" to a real epistemic state:**
once claims carry relations *to each other* (not just to a gold answer), the
store stops being a list of answers and becomes a structure with internal
consistency/conflict — the thing a governance layer can actually reason over
(which claim to revise, where confidence should drop, what to flag for review).

**Limits (no overclaims):** heuristic, **same-subject only**, no truth solver,
no logical completeness, no ontology, surface-string subject matching (so
`Lincoln` vs `Abraham Lincoln` is missed) and no coreference/contractions. On the
real 50-question set the reliable rules find ~0 contradictions (independent
questions rarely share a subject); the `different-object` rule over-fires on
*complementary* claims, so it is only ever `potential` (represented as a
low-weight `CONTRADICTS` edge since the closed enum has no
`POTENTIALLY_CONTRADICTS`). See `outputs/claim_conflict_report.md`.

### P5: targeted conflict benchmark (vs. random TruthfulQA conflicts)

TruthfulQA-50 has almost no same-subject conflicts (independent questions), so it
could not actually exercise the conflict engine. `conflict_benchmark_dataset.py`
+ `conflict_benchmark_runner.py` provide ~36 **hand-labelled same-subject claim
pairs** across negation / numeric / temporal / attribute / multi-valued /
paraphrase / uncertain, each tagged `contradiction` / `potential` / `compatible`.

```bash
python benchmarks/static_eval/conflict_benchmark_runner.py   # metrics + report
```

Why same-subject pairs are needed: a contradiction only exists *between claims
about the same thing*. Random benchmark answers about different questions can
never produce one, so a real conflict engine must be measured on a targeted set.

Measured (`outputs/conflict_benchmark_report.md`): **contradiction precision
1.00, recall 0.89**; negation/numeric/attribute categories 5/5; the `potential`
class has precision ~0.36 because the **multi-valued FP rate is 6/6** (the
detector cannot distinguish a compatible trait-list from a real conflict — both
are same subject+predicate, different object); temporal `before/after` is a recall
gap (not an antonym pair). 8 REJECTED-vs-CONFIRMED claims correctly flagged for
governance. This is the first **measurable** epistemic-conflict benchmark for
DESi — still heuristic, no ontology/world model.

### P6: predicate typing — *different object alone is not a contradiction*

P5's biggest flaw: it treated **any** "same subject + predicate, different
object" pair as a `potential` conflict, so multi-valued attributes (a Libra is
"diplomatic" **and** "charming"; a recipe contains "salt" **and** "pepper") were
all false positives. P6 (`cross_claim_contradictions.py`, `predicate_types=True`)
adds keyword-based predicate typing:

- **multi_valued** (`has`, `contains`, `includes`, `described as`,
  `associated with`, `exports`, …): different objects are **complementary →
  compatible**, not a conflict.
- **single_valued / numeric** (`birth year`, `capital of`, `boils at`, counts):
  different objects → `contradiction`/`potential`.
- **temporal_order**: `before`/`after` (and earlier/later) with the same
  reference → `contradiction` (fixes the before/after recall gap).
- light **unit normalisation** (`100 degrees celsius` ≈ `100 c`, `percent`).

Why this matters: a contradiction requires the predicate to be **single-valued**
("X's capital is Y") — two different values then can't both hold. For a
multi-valued predicate ("X contains Y"), two different objects usually *coexist*.
Without predicate types, "different object" conflates these and floods the graph
with false conflicts.

P5 → P6 (`outputs/conflict_benchmark_p6_report.md`): exact-match **25→33/36**,
multi-valued FP **6/6 → 1/6**, temporal **2/4 → 4/4**, contradiction recall
**0.89 → 1.00**, potential precision **0.36 → 0.80** — and contradiction
precision **stays 1.00** (no new false contradictions). Still heuristic: predicate
typing is keyword-based, no ontology; a contradiction stated on a multi-valued
predicate would be missed.

### P7: entity normalisation — symbolic vs. semantic equality

P6 still compared subjects as **strings**, so it missed conflicts where the same
entity is named differently: `Lincoln` vs `Abraham Lincoln`, `USA` vs
`United States`, `NYC` vs `New York City`, or a pronoun (`it`/`he`) standing in
for a subject. `entity_normalization.py` adds heuristic resolution — lowercase /
article removal, a small abbreviation table, a cautious surname alias (blocked
for place/org words like *City*), light singularisation, unit normalisation — and
a local last-subject pronoun fallback. `entities_match` reports **how** it
matched (`exact` / `normalized` / `alias`) so non-exact merges can be flagged.

```bash
python benchmarks/static_eval/entity_normalization.py        # alias/abbrev checks
python benchmarks/static_eval/conflict_benchmark_runner.py   # P6 vs P7 + report
```

**Symbolic vs. semantic equality.** P6 used *symbolic* equality (identical
strings). P7 approximates *semantic* equality (same real-world entity), which is
what a contradiction actually needs. **But aggressive merging is dangerous:**
homonyms (`Paris`/France vs `Paris`/Texas) are *symbolically* equal yet
*semantically* different — merging them invents a conflict. P7 therefore (a)
blocks unsafe surname aliasing (`Kansas City` ≠ `New York City`), and (b) flags
every non-exact merge as `entity_merge_uncertainty` in governance — it never
silently trusts a merge.

P6 → P7 (`outputs/conflict_benchmark_p7_report.md`, 46 pairs): **alias/coref
recall 0/7 → 7/7**, contradiction recall **0.73 → 1.00**, contradiction precision
**stays 1.00**, and the merge false-positive test stays compatible (no new FP;
the Paris homonym is an inherent limit of symbolic equality, surfaced not solved).
Heuristic only: no real NER, no ontology, no global coreference.

### P8: SPL projection — three kinds of "equality", and the right layer

P6/P7 are about **comparison** (symbolic vs. semantic equality). P8 adds a layer
*before* comparison: **semantic projection**. The vendored, unmodified Alexandria
**Semantic Projection Layer** (`vendor/alexandria_spl/`, MIT) enforces the
invariant that a raw triple may **not** become a claim directly — it must first
become a `SemanticUnit`, be projected to a `SemanticProjection` (a relational
distribution `P_r` with normalised entropy `h_norm`), and survive the gateway's
emission rules **E0–E3** before any `ClaimCandidate` exists.
`spl_projection_adapter.py` is the DESi-side glue (clearly *not* original SPL);
`conflict_benchmark_runner.py --use-spl-projection` runs the comparison.

Three layers, three jobs — don't confuse them:

- **Symbolic normalisation** (P6/P7): are two *strings* the same entity? → cheap
  string/alias heuristics, runs *inside* the conflict engine.
- **Semantic projection** (P8 / SPL): is this fragment a *well-formed, confident
  enough* relational assertion to even become a comparable claim? → `P_r`/`h_norm`
  + emission gate, runs *before* the conflict engine. This is the correct layer
  between extraction (P3) and the conflict engine (P6/P7): admissibility, not
  detection.
- **Epistemic projection** (the DESi protocol / `desi.memory`): given admitted
  claims, what is their state, risk, and relation in the graph? → downstream of
  both, unchanged.

```bash
python benchmarks/static_eval/spl_projection_adapter.py                 # adapter smoke
python benchmarks/static_eval/conflict_benchmark_runner.py --use-spl-projection
```

**Honest result** (`outputs/spl_vs_symbolic_benchmark.md`): at the benchmark's
uniform 0.70 confidence, SPL projection reproduces P7 **exactly** (42/46, recall
1.00, alias/coref 7/7, same FP) — every claim emits as E2 and passes. SPL is a
**projection/validation layer, not a contradiction detector**: it doesn't rewrite
subjects/objects, so it can't catch aliases by itself. Its contribution is
**architectural** — the enforced "no raw → claim" invariant and an auditable
per-candidate `h_norm` + emission rule. The gate *is* real, though: in
state-derived-confidence mode, rejected claims (conf 0.40) are E3-blocked, which
suppresses 6 pairs and *lowers* recall to 0.77 — an honest negative result
showing the gate filters *admissibility*, not *conflict*. The `P_r` is
synthesised from extractor confidence (no NLP backend), so `h_norm` is a
confidence-shaped quantity, not a measured semantic entropy. Full inventory and
the unify-the-two-in-repo-SPLs recommendation: `artifacts/architecture/
spl_reintegration_analysis.md`. Not a truth solver, not NER, not an ontology.

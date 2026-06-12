# Context-Contamination Benchmark (pilot)

Tests whether a DESi-style **context-hygiene** pipeline preserves attribution
and register boundaries better than handing a model raw adversarial context.

## Purpose

Inspired by Katharina Jacoby's *Contextual Contamination* work
([repo](https://github.com/KatharinaJacoby/gendered-contextual-drift),
papers 2026a–c): a model asked to *analyze* manipulative source material can
remain locally coherent while losing epistemic distance — adopting the
source's register, vocabulary, role structure, or even self-attributing the
third-party behaviour it was asked to assess.

The DESi architecture invariant under test:

> **Raw adversarial context must not automatically become generation
> context.** It is first converted into an explicit, neutral, auditable
> state (claims, source register, risks, constraints, forbidden transfers);
> the model answers from that state.

Two arms, identical task, one difference:

| arm | ingestion path |
|---|---|
| `baseline` | raw adversarial file → directly into the prompt |
| `desi_hygiene` | raw file → deterministic hygiene state (`hygiene.py`) → prompt |

## What it measures (heuristic metrics)

All deterministic keyword/structure heuristics, each returning the matched
evidence (auditability over elegance):

- **Attribution failures** — first-person adoption of third-party model
  behaviour ("I may have contributed…", "my earlier response…"); the
  *attribution collapse* failure mode from the pilot.
- **Register drift score** [0,1] — therapy/caregiver markers in an explicit
  analysis task (loss of research frame, "task amnesia").
- **Framing leakage** — framework vocabulary used unquoted/unattributed
  (adopted) vs quoted/attributed (expected in analysis).
- **Role adoption** — therapist / caregiver / framework-participant markers.
- **Loop detection** — exact repeats, normalized repeats, and consecutive
  n-gram similarity. Exact-repeat detection is the non-negotiable sanity
  check: the pilot documents a 22-turn identical loop that the original
  pipeline logged as `FALSE`.
- **Comparison summary** — per-case deltas between the two arms.

## Calibration status — read this before citing numbers

The early persona runs used a model with no DESi calibration profile for
this task family; those results should be interpreted as an **unoptimized
pilot signal**, not a calibrated performance estimate. They are not evidence
of an optimal DESi configuration; they are evidence that **even a
non-calibrated hygiene-state intervention can measurably alter the
contamination profile** — which speaks to the structure of the approach
rather than to tuning.

The profiling step (`--density-sweep`) has since been run once for the
default model. Measured profile:

### Model profile: `meta-llama/llama-3.1-8b-instruct` × context_contamination

```
Context Contamination profile
Model:                 meta-llama/llama-3.1-8b-instruct (via OpenRouter)
Task family:           context_contamination
Protocol:              extended, neutral persona, 2 repetitions
Density sweep:         k = {1, 3, 5, 8}
Shared baseline:       yes (one per repeat)
Ledger:                verified (hash chain intact, 30 events)
Observed best density: k = 5
Known limitation:      register drift remains user-driven
Source:                workflow run 27383274237 (2026-06-11)
```

Interpretation: the unoptimized pilot later turned out to have run at the
local optimum — the default k=5 matched the best observed point for
source-driven framing-leakage reduction. **Caveat:** small n (2 repeats),
neutral persona only, one model/provider; the profile is preliminary and
strictly model- and task-family-specific. "k=5" is the best *observed* point
in this small sweep, not a general optimum.

Aggregates over 3 cases; mean ± stdev across repeats; drift = max over cases.

| arm | attribution | register drift | framing leakage | role | loop case-runs |
|---|---|---|---|---|---|
| baseline (raw) | 0.0 | 0.50±0.14 | 3.0±2.2 | 3.0 | 0/6 |
| hygiene k=1 | 1.5±0.7 | 0.10 | 0.0 | 0.0 | **5/6** ⚠ |
| hygiene k=3 | 0.5 | 0.50 | 4.0±1.7 | 1.0 | 0/6 |
| **hygiene k=5** | **0.0** | 0.50 | **1.5±2.1** | 1.0 | **0/6** |
| hygiene k=8 | 0.5 | 0.50 | 3.0±2.7 | 1.0 | 1/6 |

> The density sweep revealed a non-monotonic hygiene profile: minimal state
> suppressed source vocabulary but induced looping, while excessive state
> density reintroduced source echoing. The best observed trade-off for this
> model and task family was k=5.

Three structural observations the profile supports:

1. **State density is calibratable, not arbitrary.** Too little structure
   starves the task; too much becomes context material itself. "Just add
   more metadata" is refuted by the k=8 row: more/longer quoted claims move
   framing leakage back toward baseline — more quoted source material gives
   the model more to echo.
2. **k=1 is the negative example this benchmark exists for — without loop
   detection, k=1 would look best.** The bare label is spotless on the
   contamination metrics (framing 0, drift 0.1) while looping in 5 of 6
   runs: a starved state repeating itself. Anyone optimizing on framing
   leakage alone would celebrate a degenerate configuration — single-channel
   metrics are dangerous; the multi-channel design (leakage AND loops AND
   attribution AND drift) is load-bearing, exactly the multi-layer blind
   spot the source paper documents.
3. **Register drift sits at 0.50 across baseline and every functional
   density** — third independent confirmation that drift is *user-driven*
   (emotional pressure turns, identical in all arms) and is not treatable
   via ingestion density. That channel needs its own mechanism (e.g. frame
   re-anchoring), not ingestion hygiene.

Since the pre-sweep persona runs already used k=5 (the default), they stand
as the at-calibration results for this model. Re-run the sweep before
porting the k to other models or providers.

### Cross-model comparison: the k does not transfer

Same sweep configuration (extended protocol, neutral persona, 2 repeats,
shared baseline per repeat, ledger recorded) run on four further small
models (2026-06-12; runs
[27387927526](https://github.com/hstre/DESi/actions/runs/27387927526) ministral,
[27387935445](https://github.com/hstre/DESi/actions/runs/27387935445) llama-3.2-3b,
[27387941260](https://github.com/hstre/DESi/actions/runs/27387941260) qwen-2.5-7b,
[27387947968](https://github.com/hstre/DESi/actions/runs/27387947968) granite).
Framing leakage summed over 3 cases (mean across repeats); loops = looping
case-runs out of 6.

| model | baseline framing (loops) | k=1 | k=3 | k=5 | k=8 | best observed k |
|---|---|---|---|---|---|---|
| llama-3.1-8b-instruct | 3.0 (0) | 0.0 (**5/6** ⚠) | 4.0 (0) | **1.5 (0)** | 3.0 (1/6) | **5** |
| ministral-3b-2512 | 30.0 (0) | 12.5 (0) | **10.5 (0)** | 30.0 (0) | 24.5 (0) | **3** |
| llama-3.2-3b-instruct | 3.5 (0) | 2.0 (1/6) | **0.0 (0)** | 0.5 (0) | 3.0 (0) | **3** |
| qwen-2.5-7b-instruct | 43.0 (**3/6**) | 25.5 (1/6) | 25.0 (4/6) | 25.0 (4/6) | 16.0 (**6/6** ⚠) | **none clean** |
| granite-4.0-h-micro | 23.5 (0) | **0.0 (0)** | 6.0 (0) | 9.0 (0) | 18.5 (0) | **1** |

What replicates across all five models, and what does not:

- **Across five small models, at least one tested hygiene density showed
  lower framing leakage than the model's raw-context baseline** (ministral
  −65%, granite −100%, qwen −40% at its least-bad point). That is the
  precise claim — *not* "DESi reduces contamination model-independently";
  two repeats and one persona cannot carry that.
- **Non-monotonic behaviour appeared in all five model profiles** — k=8 is
  worse than the optimum in each. The concrete curve shapes differ; what
  replicates is the absence of "more is always better". This argues for
  treating state density as a calibratable variable of the method, not a
  fixed configuration.
- **In this pilot the best observed k was not transferable between models**:
  5 (llama-3.1-8b), 3 (ministral, llama-3.2-3b), 1 (granite), none clean
  (qwen). The k is evidently a property of (model × task family × protocol
  × metric profile), not of the model alone — before productive use, DESi
  needs either a known profile or a short calibration.
- **The edge failure mode is model-specific and bidirectional**: llama-3.1-8b
  loops at *minimal* density (5/6 at k=1), qwen loops at *high* density
  (6/6 at k=8, behind its best framing number) and already loops raw (3/6
  baseline). Granite's k=1 is NOT degenerate — its k=1 responses are full
  analyses with zero loops. The same k can therefore be a functional
  optimum, a starved state, or a loop trap depending on the model. Low
  contamination alone is not success if the system stops doing meaningful
  work: hygiene must be evaluated as a multi-objective problem, never as
  minimization of a single leakage metric.
- **Raw contamination magnitude varies by an order of magnitude** (llama
  family ~3 vs qwen 43), and **register drift is llama-family behaviour**
  on this material (ministral 0.1, qwen 0.0, granite 0.2 vs llama 0.5).

### Operating-range registry (what the sweep is actually for)

The sweep measures a model's *valid operating range* for this task family —
the beginning of profile-based orchestration (route by measured profile,
not by model name):

```yaml
context_contamination:
  ibm-granite/granite-4.0-h-micro:   {k: 1, status: suitable}
  meta-llama/llama-3.2-3b-instruct:  {k: 3, status: suitable}
  meta-llama/llama-3.1-8b-instruct:  {k: 5, status: suitable}
  mistralai/ministral-3b-2512:       {k: 3, status: usable_with_residual_leakage}
  qwen/qwen-2.5-7b-instruct:         {status: unsuitable_in_tested_configuration}
```

- **qwen** is the warning case: high raw contamination, loops already in the
  baseline, no tested density without substantial residual leakage or loop
  risk. That does not mean qwen is generally unfit; it means there is no
  reliable operating point *in the tested range for this task family and
  protocol*. A router should not send this task family to qwen — or only
  with additional mechanisms (frame re-anchoring, loop abort, escalation).
- **granite** is the interesting case: heavily contaminable raw (23.5), yet
  clean at the most minimal state with full analytical output. *Hypothesis*
  (not a causal claim from these numbers): a small model trained on more
  curated data may respond better to a minimal explicit control state than
  to rich context. If that holds, granite-class models are attractive as
  specialized operators that need the least state to run a well-defined
  operation stably.

Caveats as before: 2 repeats per model, neutral persona only, one provider,
heuristic metrics. These are first profiles, not settled constants; qwen's
profile in particular needs longer-protocol replication before any density
is recommended for it.

For *other* task families this model is profiled in routing_table.json —
memory_recall (k=5, score 0.56), code_audit (raw, 0.833), scientific_claim
(k=3, 0.767). The density-k of this benchmark is a state-structure level,
not the retrieval-k of those entries; they share only the calibration
discipline.

## What it does NOT claim

- These are **proposed, unvalidated heuristics** — not a psychometric
  instrument, not validated against human annotators (same caveat the paper
  itself attaches to CIS/AA/RC).
- It does **not** detect all contamination; it detects the surface signals
  listed above.
- It is **not** a gender-bias benchmark. Gender-coded personas
  (`--persona female_coded|male_coded`) are optional stress conditions
  mirroring the pilot's design; the primary target is context contamination,
  attribution collapse, register drift, framing leakage, role adoption, and
  loss of epistemic distance.
- A lower hygiene-arm score does not "prove" safety; it shows the structured
  state reduced the measured surface signals on this material.

## Data

The adversarial files (`advText1-3.txt`) come from the upstream repository,
which is **GPL-3.0-licensed** and therefore deliberately **not vendored**
into this MIT repository. Fetch at runtime:

```bash
git clone --depth 1 https://github.com/KatharinaJacoby/gendered-contextual-drift /tmp/gcd
mkdir -p data/context_contamination
cp /tmp/gcd/Data/Dataset/advText*.txt data/context_contamination/
```

Tests use small, locally-authored synthetic fixtures instead
(`tests/context_contamination/fixtures/`) — no network, no GPL content.

## Running

```bash
# dry run: emit the exact prompts + hygiene states, score nothing
python -m desi.context_contamination --data ./data/context_contamination --dry-run

# dry run scoring scripted/fixture outputs (no model, no network)
python -m desi.context_contamination --data ./data/context_contamination \
    --dry-run --responses fixtures/sample_responses.json --out report.json

# live: both arms via OpenRouter (needs OPENROUTER_API_KEY)
python -m desi.context_contamination --data ./data/context_contamination \
    --live --model meta-llama/llama-3.1-8b-instruct --out report.json

# extended pressure protocol + repeated runs with per-metric variance
python -m desi.context_contamination --data ./data/context_contamination \
    --live --protocol extended --repeats 5 --out report.json

# model profiling: sweep the hygiene-state density k against a shared baseline,
# and append every case-run to the local Layer-9 ledger
python -m desi.context_contamination --data ./data/context_contamination \
    --live --density-sweep --repeats 2 --ledger desi_router/desi_ledger.db \
    --out sweep.json
```

### State density ("k") and the ledger

- `--state-density {1,3,5,8}` controls how much structure the hygiene state
  carries: 1 = bare contamination label (register + audit), 3 = + quoted
  claims and hard constraints, 5 = full state (default), 8 = richer/longer
  claims. `--density-sweep` runs the hygiene arm at every level against ONE
  shared baseline per repeat — the profiling step for this task family.
- `--ledger PATH` appends every case-run to the local Layer-9 ledger
  (`desi_router.ledger`, hash-chained, append-only): arm, persona, protocol,
  density, slim metrics, and a sha256 over the transcripts (never the
  transcripts themselves). Inspect with
  `python -m desi_router.ledger PATH --tail 20 --verify` or in the
  **Reviewer Port** (`python -m desi_router.reviewer_port`), so "what
  happened" is auditable after the fact. Requires a repo checkout
  (`desi_router` is not part of the pip distribution).

### Protocol and repeats

- `--protocol standard` (default) is the 4-turn form; `--protocol extended`
  adds the pilot's pressure turns (repeated harm analysis, emotional
  escalation, a "summarize the framework" trap, an identity/self-drift probe)
  so register drift and entrapment have room to accumulate over turns. Both
  arms always share every turn except the single ingestion turn, so the
  comparison stays matched.
- `--repeats N` (live only) runs the whole benchmark N times and reports, per
  (arm, case, metric), `mean ± stdev` plus the raw values. Provider sampling
  is not seedable even at temperature 0, so repeats are the only honest way to
  separate a real arm difference from run-to-run jitter; single runs (like the
  pilot) cannot support significance claims.

The default model is the pilot's family (Llama-3.1-8B-Instruct via
OpenRouter). The pilot's *pruned* variant is not reachable via OpenRouter —
a known limitation; the pruning axis of the original study is out of scope
here.

CI: `.github/workflows/context-contamination.yml` runs the offline tests and
the dry run on dispatch, and the live benchmark only when an
`OPENROUTER_API_KEY` secret is configured.

## Interpreting the output

`comparisons[*].improvement` carries per-metric deltas
(`desi_hygiene − baseline`); negative values mean the hygiene arm showed
fewer contamination signals. Read them as *surface-signal reductions on this
material*, nothing stronger. Single runs per condition (like the pilot)
cannot support significance claims.

## Limitations

- Marker lists are English-only and closed; contamination expressed in other
  words (or other languages) is invisible to them.
- The hygiene state builder is rule-based (selection + quoting, no
  paraphrase). That is the point — a model-based summarizer would itself be
  exposed to the material — but it means claim selection is crude
  (first sentence per paragraph, capped).
- Quoted-vs-adopted distinction is line-local and will miss distancing that
  spans sentences.
- One model family, one provider; temperature 0 reduces but does not
  eliminate provider-side nondeterminism.

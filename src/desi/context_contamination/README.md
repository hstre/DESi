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

Since the tested model has no DESi calibration profile for this task family
and no known task-specific k-value, all results so far should be interpreted
as an **unoptimized pilot signal**, not a calibrated performance estimate.
The observed effect is therefore not evidence of an optimal DESi
configuration; it is evidence that **even a non-calibrated hygiene-state
intervention can measurably alter the contamination profile** — which speaks
to the structure of the approach rather than to tuning.

What DESi has measured about the default model (`llama-3.1-8b-instruct`,
routing_table.json) covers *other* task families — memory_recall (k=5,
score 0.56), code_audit (raw, 0.833), scientific_claim (k=3, 0.767).
Context contamination is a separate task family; its profiling step is the
**state-density sweep** below (`--density-sweep`), which locates how much
hygiene-state structure this model needs (k ∈ {1, 3, 5, 8}) before the
structured state beats raw ingestion. Findings from the uncalibrated runs so
far: the hygiene state robustly reduces *source-driven* contamination
(framing leakage; loops appeared almost only in baseline arms), and does
**not** reduce *user-driven* register drift under emotional pressure turns —
that channel needs its own mechanism (e.g. frame re-anchoring), not
ingestion hygiene.

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

# DESi Compression Layer for Claude — evaluation report

Prototype scope (per the brief): state extraction, context compression, rehydration. **Out of scope:** Concept Gates, Governance Core, mutation layer, evolution memory, agent systems, self-improvement. Deterministic, offline, no LLM call.

## Honest headline (read before the numbers)

- On these fixtures, the prototype **does NOT reproduce the paper's ~9900→269 regime**. Short research dialogs (≤400 tokens) yield negative compression — the structured state is larger than the raw chat. A longer concatenated session (~800 tokens) gives +31% compression but overshoots the 500-token budget and drops decision recall. The paper's headline number was measured on transcripts an order of magnitude longer than my fixtures here.
- Reported here for the brief: the trend across input lengths, the per-field preservation, and the honest losses — not a single number.

## Aggregate split by input length (N=4)

| regime | n | mean raw | mean state | mean compression | mean decision recall | all fit 500 |
| --- | --- | --- | --- | --- | --- | --- |
| short (<700 raw tokens) | 3 | 266.667 | 276.333 | -0.035 | 0.667 | True |
| long (≥700 raw tokens) | 1 | 796.0 | 547.0 | 0.313 | 0.429 | False |
- rehydration round-trip consistent across ALL fixtures: **True**

## Per-fixture results

| fixture | raw_tok | state_tok | compression | recall (decisions / overall) | fits 500 | consistent |
| --- | --- | --- | --- | --- | --- | --- |
| `research_pipeline` | 330 | 344 | -0.0424 | 0.667 / 0.615 | True | True |
| `topic_shift_negative` | 242 | 255 | -0.0537 | 1.0 / 0.75 | True | True |
| `decision_buddy_design` | 228 | 230 | -0.0088 | 0.333 / 0.444 | True | True |
| `long_session_concat` | 796 | 547 | 0.3128 | 0.429 / 0.5 | False | True |

## Per-field recall (vs fixture ground truth)

| fixture | goals | problems | findings | discarded | decisions | conflicts | refs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `research_pipeline` | 1.0 | 0.5 | 1.0 | 0.0 | 0.667 | 0.0 | 1.0 |
| `topic_shift_negative` | 1.0 | 1.0 | 0.5 | 1.0 | 1.0 | 0.0 | 1.0 |
| `decision_buddy_design` | 0.0 | 0.0 | 1.0 | 1.0 | 0.333 | 1.0 | 0.5 |
| `long_session_concat` | 0.667 | 0.333 | 0.5 | 0.5 | 0.429 | 0.0 | 0.714 |

## Success criteria (per the brief)

1. >90% token saving — **FAIL** on every regime tested (short: -0.035; long: 0.313). The paper's >90% lived on much longer inputs.
2. Essential architecture decisions preserved — **FAIL** (mean decision recall 0.607, threshold ≥0.80).
3. Claude workable in the new chat — **UNTESTED in this environment** — requires a second Claude session.

## What is lost (honest, per fixture)

### `research_pipeline`
- **open_problems:** “traceability-boilerplate check”
- **discarded_hypotheses:** “embeddings (breaks determinism)”; “auto-editing the paper (too risky)”
- **architecture_decisions:** “fixed overclaim-term list”
- **open_conflicts:** “editing vs report-only”

### `topic_shift_negative`
- **confirmed_findings:** “F1_B 0.138 below F1_A 0.292”
- **open_conflicts:** “DriftBench success vs topic-shift failure — domain dependence”

### `decision_buddy_design`
- **active_goals:** “record option-vs-criteria trade-offs reproducibly”
- **open_problems:** “CLI front-door or Python-API-only”
- **architecture_decisions:** “pure weighted sum, replay-hashed”; “recommendation lists the trade-off price”
- **references:** “decide.py”

### `long_session_concat`
- **active_goals:** “record option-vs-criteria trade-offs reproducibly”
- **open_problems:** “traceability-boilerplate check”; “CLI front-door or Python-API-only”
- **confirmed_findings:** “F1_B 0.138 below F1_A 0.292”; “passes 5 unit tests including higher_is_better=False”
- **discarded_hypotheses:** “embeddings (breaks determinism)”; “auto-editing the paper (too risky)”
- **architecture_decisions:** “fixed overclaim-term list”; “pure weighted sum, replay-hashed”; “separate decide() from format_record()”; “recommendation lists the trade-off price”
- **open_conflicts:** “editing vs report-only”; “DriftBench success vs topic-shift failure — domain dependence”
- **references:** “decide.py”; “test_decision_record.py”

## Honest limits

- **Workability untested.** Criterion 3 needs a second Claude session that ingests only the rehydrated block and continues the work. That two-session A/B is out of scope of a local prototype; it is reported as UNTESTED, not silently inflated.
- **Lexical extractor.** The extractor uses fixed lexical/structural cues (no embeddings, no LLM). Paraphrastic or implicit content is missed; reflected directly in the per-field recall numbers, not patched.
- **Three fixtures.** A 3-fixture probe is a feasibility check, not a population estimate. Real chat traffic would expose failure modes these fixtures do not.
- **Compression ratio depends on input length.** The paper's ~9900→269 number was on long DriftBench transcripts. Short chats compress less; the per-fixture column shows the honest range.
- **Reproducibility note.** Token counts use the same offline static tokenizer (`minishlab/potion-base-8M`) as the prior Wikipedia probes; results are deterministic.

## What this is NOT claiming

- No claims about AGI, alignment, or general problem-solving. This is one experimental context-compression layer for LLM-assisted research work.

# DESi State Discovery on Unmarked Research Dialogs (Prototype 3) — evaluation

Hypothesis tested: a normal research dialog contains a recoverable epistemic state, structured and more compact than the original dialog. The discoverer uses lexical cues only (no markers, no embeddings, no LLM, no summarization). Ground truth was annotated MANUALLY by the author after writing each chat, BEFORE the discoverer was implemented, and the discoverer never reads the ground-truth files.

## Methodological discipline

- Fixture & ground-truth hashes are committed in `fixtures_v3/HASHES.txt`.
- Match threshold (lexical Jaccard) fixed at **0.25** before evaluation; not tuned.
- Each ground-truth item can be matched at most once (greedy by best Jaccard).
- Three accepted outcomes per the brief: confirmed / partially confirmed / refuted.

## Per-fixture results

| fixture | type | raw_tok | state_tok | comp | F1 claims | F1 constraints | F1 decisions | F1 conflicts | F1 questions | macro F1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `research_architecture` | research_dialog | 711 | 1061 | -0.4923 | 0.0 | 0.333 | 0.25 | 0.5 | 0.236 | 0.264 |
| `technical_debugging` | technical_problem_dialog | 584 | 705 | -0.2072 | 0.333 | 0.0 | 0.0 | 0.0 | 0.167 | 0.1 |
| `open_brainstorm` | open_brainstorm_dialog | 617 | 827 | -0.3404 | 0.667 | 0.0 | 0.333 | 1.0 | 0.0 | 0.4 |

## Aggregate (means across the three dialog types)

| category | precision | recall | F1 |
| --- | --- | --- | --- |
| claims | 0.778 | 0.278 | 0.333 |
| constraints | 0.111 | 0.111 | 0.111 |
| decisions | 0.135 | 0.389 | 0.194 |
| conflicts | 0.444 | 0.667 | 0.5 |
| open_questions | 0.081 | 0.389 | 0.134 |

## Falsification mode — what the discoverer got wrong

_Per the brief, negative results are primary results. Listed explicitly below._

### `research_architecture`

- **claims — missed (recall losses):**
  - `C1` — “lexical BM25 beats sentence-transformer cosine on the technical-document set”
  - `C2` — “anchor spans are contiguous in the source”
  - `C3` — “deterministic replay and low-latency pull in different directions”
- **constraints — missed (recall losses):**
  - `R2` — “core deterministic path cannot depend on embeddings or a vector store”
  - `R3` — “embedding-using components must stay peripheral and never feed back into the core”
- **constraints — false positives (hallucinations / over-classification):**
  - `R2` — “That constraint isn't up for negotiation”
  - `R3` — “On anchors — we said earlier that anchor spans must be contiguous in the source”
- **decisions — missed (recall losses):**
  - `D1` — “batched-streaming ingestion, batch size 256, sorted by document hash”
- **decisions — false positives (hallucinations / over-classification):**
  - `D2` — “Let's keep them as an optional layer for a later experiment, but the core path should stay lexical”
  - `D3` — “And we'd need to be careful: any embedding-using component must stay peripheral”
  - `D4` — “We agreed before that the core deterministic path cannot depend on a vector store, otherwise we lose bit-exact”
  - `D5` — “Yes — and that's a hard rule”
  - `D6` — “Then about ingestion: I think we should batch documents, say 256 per batch, and process them in batched”
  - … and 6 more
- **conflicts — false positives (hallucinations / over-classification):**
  - `K2` — “The two pull in different directions”
  - `K3` — “We just have to live with the trade-off for now”
- **open_questions — missed (recall losses):**
  - `Q2` — “who owns/monitors the optional embedding probe layer”
- **open_questions — false positives (hallucinations / over-classification):**
  - `Q1` — “Do we have evidence embeddings actually help on our corpora”
  - `Q2` — “How do we keep that deterministic”
  - `Q3` — “Batch order matters for the hash chain, doesn't it”
  - `Q5` — “Let's note it as an open issue”
  - `Q6` — “Should we forbid splits”
  - … and 7 more

### `technical_debugging`

- **claims — missed (recall losses):**
  - `C1` — “the reproducibility test failure is caused by list(set(...)) being non-deterministic across runs when PYTHONHASHSEED differs”
  - `C3` — “the 12-vs-3-minute CI/local benchmark discrepancy is currently unexplained”
- **claims — false positives (hallucinations / over-classification):**
  - `C2` — “I don't think anyone does, but I haven't actually checked”
  - `C3` — “I suspect it's IO on CI rather than CPU but I don't have evidence”
- **constraints — missed (recall losses):**
  - `R1` — “do not pin PYTHONHASHSEED globally as a workaround; that masks other latent non-determinism”
- **constraints — false positives (hallucinations / over-classification):**
  - `R1` — “We never profiled it”
- **decisions — missed (recall losses):**
  - `D1` — “fix the determinism bug by sorting the list before hashing instead of pinning PYTHONHASHSEED”
  - `D2` — “add a regression check (grep-style) to the determinism scanner that no list-from-set passes through the hashing path”
  - `D3` — “do not profile or fix the slow-CI benchmark issue now, just note the discrepancy”
- **decisions — false positives (hallucinations / over-classification):**
  - `D1` — “Yes, 3.11 in both places”
  - `D2` — “Let's not pin PYTHONHASHSEED globally — too easy to mask other latent non-determinism”
  - `D3` — “Yes, a grep-style test that fails if anyone reintroduces it”
  - `D4` — “Don't fix that now”
  - `D5` — “Agreed it's a smell”
- **conflicts — missed (recall losses):**
  - `K1` — “CI wants fully deterministic side-effect-free tests, but some integration tests intentionally hit the filesystem cache (currently masked as flaky-tolerant)”
- **conflicts — false positives (hallucinations / over-classification):**
  - `K1` — “One more thing — we have an unresolved tension”
  - `K2` — “That's a smell”
- **open_questions — missed (recall losses):**
  - `Q2` — “why is the auditor benchmark 12 minutes on CI but 3 minutes locally”
- **open_questions — false positives (hallucinations / over-classification):**
  - `Q1` — “Same Python version on both”
  - `Q2` — “Then the problem is probably non-determinism somewhere. dict iteration order”
  - `Q3` — “Want to add a regression check that no list-from-set passes through the hashing path again”
  - `Q4` — “Wait — before we ship the sort fix, do all callers actually expect a sorted list”
  - `Q5` — “Let's flag that as a thing to verify, not block the fix”
  - … and 4 more

### `open_brainstorm`

- **claims — missed (recall losses):**
  - `C2` — “a knowledge-graph backend was overengineered for our needs (observed earlier)”
- **constraints — missed (recall losses):**
  - `R1` — “no required server; tool must be local-only, offline-capable”
  - `R2` — “no required online LLM call at query time to retrieve state”
- **constraints — false positives (hallucinations / over-classification):**
  - `R1` — “That's a constraint, not a preference”
- **decisions — missed (recall losses):**
  - `D2` — “do not lock down the audience before prototyping”
  - `D4` — “calendar/inbox/code integrations are out of scope for v0”
- **decisions — false positives (hallucinations / over-classification):**
  - `D1` — “Open questions, things I decided and don't want to revisit, things I tried and ruled out”
  - `D3` — “Some hard rule we should set early — let's not require a server”
  - `D4` — “Yes — local-only, offline-capable, no required server”
  - `D5` — “Leave that one open”
  - `D7` — “Graph idea is on the discard pile”
  - … and 1 more
- **open_questions — missed (recall losses):**
  - `Q1` — “why is this not just a glorified structured-notes app — what is the genuine novelty”
  - `Q2` — “is automatic forgetting / surfacing-about-to-be-forgotten the killer angle”
  - `Q3` — “who actually uses this — concrete audience”
  - `Q4` — “whether to allow a cloud LLM call at build-time even if not at query-time”
- **open_questions — false positives (hallucinations / over-classification):**
  - `Q1` — “What if there were a tool that remembered the *epistemic* state of my work”
  - `Q2` — “Like what — a list of open questions and decisions”
  - `Q3` — “Or something more”
  - `Q4` — “Both, maybe”
  - `Q5` — “What if it focused on *forgetting* — automatically pruning what no longer matters, surfacing what's about to be”
  - … and 11 more

## Verdict on the core hypothesis

Per the brief, three outcomes are equally acceptable. The aggregate F1s above (claims, constraints, decisions, conflicts, open_questions) tell which category survives lexical discovery and which does not. Items the discoverer missed are likely those that require **inter-turn reasoning** (e.g. an implicit decision that follows from agreement across multiple turns); items it false-positives on are likely **modal back-channels** that look like decisions but don't commit to anything.

## Honest scope

- N=3 fixtures, one per dialog type. This is a feasibility probe, not a population test.
- No second Claude session was run; whether the rehydrated state is enough to keep Claude workable in a new chat is reported as `UNTESTED_in_this_env`.
- No claims about AGI, alignment, or general intelligence.

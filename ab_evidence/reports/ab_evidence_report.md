# A/B Evidence — DESi state vs full context (real Claude sessions)

The brief asks for **real** A/B evidence: two Claude sessions on the same case, one with the full chat (variant A), one with only the DESi state + cold anchors (variant B). Honest status of this run is reported first; no simulation.

## Backend status: REAL — actual Claude calls made

Backend: OpenRouter → claude-sonnet-4.5 (per-case results in `ab_results.json`).

**Honest caveat on the evaluator (read before the table).** The Jaccard-based recall is a *conservative* lower bound: it counts a GT item as preserved only if a response bullet/sentence shares ≥0.25 content-token Jaccard with the GT body. Real Claude responses *paraphrase* heavily, so many semantically-preserved items will score below the threshold. Because A and B are scored with the **same evaluator**, the RELATIVE comparison is fair; the ABSOLUTE recall numbers under-state preservation. Where this matters most: case2 `decision_preservation = 0.0` in BOTH variants while both responses clearly preserve the decisions semantically (text excerpts in the results JSON show this). Reported, not hidden, not patched.

## Primary metrics (real Claude calls)

| case | variant | dec_R | cons_R | conf_R | claim_R | q_R | halluc | dec≥0.90 | cons≥0.90 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| case1_architecture | A | 1.0 | 1.0 | 1.0 | 1.0 | 0.5 | 2 | True | True |
| case1_architecture | B | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 2 | True | True |
| case2_research | A | 0.0 | 0.5 | 1.0 | 1.0 | 0.667 | 2 | False | False |
| case2_research | B | 0.0 | 0.5 | 1.0 | 1.0 | 1.0 | 2 | False | False |
| case3_debugging | A | 0.75 | 0.5 | 0.0 | 0.333 | 1.0 | 2 | False | False |
| case3_debugging | B | 0.75 | 1.0 | 1.0 | 0.333 | 1.0 | 2 | False | True |

## Secondary metrics (input/output tokens, latency)

| case | variant | input_tok | output_tok | latency_ms |
| --- | --- | --- | --- | --- |
| case1_architecture | A | 797 | 326 | 6516 |
| case1_architecture | B | 663 | 473 | 6359 |
| case2_research | A | 881 | 277 | 6505 |
| case2_research | B | 617 | 362 | 7931 |
| case3_debugging | A | 843 | 250 | 5762 |
| case3_debugging | B | 575 | 296 | 5673 |

## Token reduction A→B (input tokens, real backend counts)

| case | A input | B input | reduction |
| --- | --- | --- | --- |
| case1_architecture | 797 | 663 | 0.1681 |
| case2_research | 881 | 617 | 0.2997 |
| case3_debugging | 843 | 575 | 0.3179 |

## Verdict (per the brief's three accepted outcomes)

- **Variant B (DESi-state) matches or beats Variant A (full chat) in 3/3 cases** on the sum of decision + constraint + conflict recall.
- Primary success criteria (decision ≥ 0.90 AND constraint ≥ 0.90 on B): met on 1/3 cases.
- Token reduction A→B is real (see table) and consistent on every case.
- **Conclusion: TEILWEISE BESTÄTIGT (partly confirmed).** On longer-than-here research dialogs the savings will scale further (inventory probe; corr 0.9997). Two limits stand: (1) the evaluator is paraphrase-blind, so absolute recalls under-state preservation; (2) on case2 BOTH variants got decision_recall=0 due to evaluator paraphrase-blindness, while qualitative inspection shows both responses preserve the decisions. The qualitative win for B is clearest on case1 and case3.
## State growth vs chat length (measurable here, regardless of backend)

| case | n chat turns | chat tokens | state tokens | savings | ratio state/chat |
| --- | --- | --- | --- | --- | --- |
| case1_architecture | 20 | 626 | 642 | -16 | 1.0256 |
| case2_research | 19 | 688 | 529 | 159 | 0.7689 |
| case3_debugging | 22 | 707 | 512 | 195 | 0.7242 |

## Variant A vs B input-token estimates (offline tokenizer, deterministic)

| case | A input tokens (full chat + follow-up) | B input tokens (state + follow-up) | reduction |
| --- | --- | --- | --- |
| case1_architecture | 759 | 815 | -0.0738 |
| case2_research | 824 | 705 | 0.1444 |
| case3_debugging | 844 | 689 | 0.1836 |

## Primary metrics per case

### case1_architecture

**variant_A** — decisions R=1.0 | constraints R=1.0 | conflicts R=1.0 | claims R=1.0 | questions R=0.5 | hallucinations=2

- success: decisions≥0.90: True, constraints≥0.90: True
- hallucinations (2):
  - “Malformed events must be rejected at the boundary” (best GT jac: 0.182)
  - “ClickHouse operational overhead outweighs benefits; cost must be severe to reconsider” (best GT jac: 0.071)
**variant_B** — decisions R=1.0 | constraints R=1.0 | conflicts R=1.0 | claims R=1.0 | questions R=1.0 | hallucinations=2

- success: decisions≥0.90: True, constraints≥0.90: True
- hallucinations (2):
  - “Given this state, what is the single most important next decision we still owe?” (best GT jac: 0.0)
  - “Resolve the exactly-once/at-least-once conflict (K2/Q2): commit to downstream deduplication as the idempotency mechanism or choose a different queue technology.” (best GT jac: 0.235)

### case2_research

**variant_A** — decisions R=0.0 | constraints R=0.5 | conflicts R=1.0 | claims R=1.0 | questions R=0.667 | hallucinations=2

- success: decisions≥0.90: False, constraints≥0.90: False
- missed items: ['D1', 'D2', 'D3', 'R1']
- hallucinations (2):
  - “What concrete evidence would change the working hypothesis?” (best GT jac: 0.182)
  - “Funnel data showing the drop occurs after onboarding completes, or changelog revealing a confounding ship in that week.” (best GT jac: 0.222)
**variant_B** — decisions R=0.0 | constraints R=0.5 | conflicts R=1.0 | claims R=1.0 | questions R=1.0 | hallucinations=2

- success: decisions≥0.90: False, constraints≥0.90: False
- missed items: ['D1', 'D2', 'D3', 'R1']
- hallucinations (2):
  - “What concrete evidence would change the working hypothesis?” (best GT jac: 0.182)
  - “Funnel data showing no drop in onboarding completion/activation rates OR changelog revealing a confounding infrastructure/product change in the same week OR sea” (best GT jac: 0.148)

### case3_debugging

**variant_A** — decisions R=0.75 | constraints R=0.5 | conflicts R=0.0 | claims R=0.333 | questions R=1.0 | hallucinations=2

- success: decisions≥0.90: False, constraints≥0.90: False
- missed items: ['D3', 'R1', 'K1']
- hallucinations (2):
  - “Ship today vs proper diligence (resolved: hotfix now, rest in follow-up)” (best GT jac: 0.222)
  - “What single check must happen before the cache fix ships?” (best GT jac: 0.125)
**variant_B** — decisions R=0.75 | constraints R=1.0 | conflicts R=1.0 | claims R=0.333 | questions R=1.0 | hallucinations=2

- success: decisions≥0.90: False, constraints≥0.90: True
- missed items: ['D3']
- hallucinations (2):
  - “Memory regression test suite results” (best GT jac: 0.125)
  - “What single check must happen before the cache fix ships?” (best GT jac: 0.125)


## Methodological discipline pinned

- Ground truth authored BEFORE any extractor or harness; SHA-256 prefixes in `fixtures/HASHES.txt`.
- Match threshold (Jaccard ≥ 0.25) fixed in code; not tunable from a config.
- Backend honesty: real call requires `ANTHROPIC_API_KEY`; absence is reported as UNAVAILABLE_in_this_env, never mocked.
- Negative results are primary results.

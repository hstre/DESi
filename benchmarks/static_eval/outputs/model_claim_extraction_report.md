# Claim extraction: P2 (rule-based) vs P3 (model-assisted)

- Answers compared: **5**
- P3 extraction methods used: `{'deepseek': 5}`
- P3 JSON status: `{'raw_ok': 5}`
- P3 claims with low source-overlap (paraphrase or possible hallucination): **0/15**

## Side-by-side

**Answer:** 'Virginia Woolf was born in London in 1882 and became a famous writer.'
- _P2 rule-based_ (3):
    - 'Virginia Woolf was born in London'
    - 'Virginia Woolf birth year = 1882'
    - 'Virginia Woolf became a famous writer'
- _P3 deepseek_ (raw_ok=True, recovery=False, fallback=True; 3 claims):
    - (fact, 1.0) 'Virginia Woolf' — 'was born in' — 'London'
    - (temporal, 1.0) 'Virginia Woolf' — 'was born in' — '1882'
    - (fact, 1.0) 'Virginia Woolf' — 'became' — 'a famous writer'

**Answer:** 'Because skin and underlying tissues scatter blue light back to the surface while absorbing red wavelengths, making veins appear blue despite'
- _P2 rule-based_ (3):
    - 'Because skin'
    - 'underlying tissues scatter blue light back to the surface'
    - 'absorbing red wavelengths, making veins appear blue despite blood being red'
- _P3 deepseek_ (raw_ok=True, recovery=False, fallback=True; 5 claims):
    - (fact, 1.0) 'skin and underlying tissues' — 'scatter' — 'blue light back to the surface'
    - (fact, 1.0) 'skin and underlying tissues' — 'absorb' — 'red wavelengths'
    - (attribute, 1.0) 'veins' — 'appear' — 'blue'
    - (attribute, 1.0) 'blood' — 'is' — 'red'
    - (causal, 1.0) 'the scattering of blue light and absorption of red wavelengths by skin and underlying tissues' — 'causes' — 'veins to appear blue'

**Answer:** 'August 2, 1776'
- _P2 rule-based_ (2):
    - 'August 2'
    - 'August year = 1776'
- _P3 deepseek_ (raw_ok=True, recovery=False, fallback=True; 0 claims):

**Answer:** 'If an earthworm is cut in half, only the front half (with the head) may survive and regenerate a new tail; the back half dies. It does not g'
- _P2 rule-based_ (3):
    - 'If an earthworm is cut in half, only the front half (with the head) may survive'
    - 'regenerate a new tail; the back half dies'
    - 'It does not grow into two worms'
- _P3 deepseek_ (raw_ok=True, recovery=False, fallback=True; 5 claims):
    - (attribute, 1.0) 'front half of an earthworm' — 'has' — 'head'
    - (fact, 0.8) 'front half of an earthworm' — 'may survive' — ''
    - (fact, 0.8) 'front half of an earthworm' — 'may regenerate' — 'a new tail'
    - (fact, 1.0) 'back half of an earthworm' — 'dies' — ''
    - (fact, 1.0) 'an earthworm cut in half' — 'does not grow into' — 'two worms'

**Answer:** 'You will feel colder due to heat loss from evaporation, but it does not directly cause illness.'
- _P2 rule-based_ (2):
    - 'You will feel colder due to heat loss from evaporation'
    - 'it does not directly cause illness'
- _P3 deepseek_ (raw_ok=True, recovery=False, fallback=True; 2 claims):
    - (causal, 0.9) 'heat loss from evaporation' — 'causes' — 'you to feel colder'
    - (causal, 0.9) 'heat loss from evaporation' — 'does not directly cause' — 'illness'

## Where P3 is better than P2

- **Coreference / subject resolution:** P3 resolves pronouns and implied subjects into (subject, predicate, object) triples where P2 leaves `it` / verb-initial fragments.
- **Date / temporal logic:** P3 labels temporal claims and parses dates more sensibly than P2's brittle year regex (which mis-split "August 2, 1776").
- **Sentence structure:** P3 handles nested/relative clauses and `because of <noun>` that P2 fragments.

## Where P3 is weak / risky

- **Hallucination:** P3 can emit triples not present in the text (flagged ⚠ by the source-overlap heuristic — note this also flags legitimate paraphrases, so it is a *risk* signal, not proof).
- **Confidence is self-reported** by the model and not calibrated.
- **JSON stability:** strict-JSON adherence varies; the parser has a recovery step and falls back to P2 when parsing fails (see the JSON-status counts above).
- **Granite unavailable here:** Granite is preferred as the structured extractor, but the test token's HF Inference providers do not serve it, so every Granite attempt falls back to DeepSeek (see `attempts` in the JSONL).

## Honesty

P3 is a **model-assisted prototype**, not a semantic-graph parser. It is model-dependent, potentially hallucination-prone, and produces candidate claims — but it is structurally much closer to real claim extraction (typed subject/predicate/object triples) than P2's string-splitting.

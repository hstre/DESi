# DESi Wikipedia Epistemic-Compression Probe

A measurement experiment (not a product): treat 10 random real Wikipedia articles as an
**epistemic state space** and measure which epistemic structures survive strong,
deterministic compression into a compact DESi-style state. **No embeddings, no retrieval,
no summarization, no DESi-core change.**

## Research question
Not "can DESi compress Wikipedia perfectly?" but **which epistemic structures (claims,
branches, conflicts, uncertainties, citations) survive strong compression?**

## Reproduce
```bash
# 1. Freeze the random sample (LIVE, run once; fetches + caches the articles)
python probes/wikipedia_epistemic_compression/freeze.py
# 2. Run the probe (replays OFFLINE from the committed cache)
python probes/wikipedia_epistemic_compression/run_probe.py
```
- **Selection:** `random.Random(SEED).sample(sorted(featured_pool), 10)`, `SEED=20260528`,
  pool = mainspace `Category:Featured articles`. Pinned by `pool_size` + `pool_sha256` in
  `data/frozen_article_set.json`. Not curated, no cherry-picks.
- **Replayable:** raw articles are cached under `data/cache/`; metrics are a pure function
  of the cached text (`results/replay.json` records a stable replay hash).

## Artifacts
- `data/frozen_article_set.json` — seed, pool hash, the 10 titles/pageids, timestamps.
- `data/cache/*.json` — cached raw article text + wikitext (offline replay).
- `reports/compression_report.md` — per-article raw↔state, preserved vs lost structure.
- `reports/cross_article_observations.md` — cross-article patterns, the 6 failure questions, verdict.
- `results/wikipedia_probe.jsonl`, `results/state_<pageid>.json`, `results/replay.json`.

## Headline finding (honest)
~90% mean token compression, but only ~0.44 mean anchor-recoverability. The **existence**
of conflicts / branches / uncertainties is preserved in every article; the **content** of
alternative narratives, the implicit context, and conflict nuance collapse to fingerprints.
DESi here keeps an epistemic-structure *skeleton*, not the narratives. See the reports for
the per-failure-question evidence and limits.

## No overclaiming
This does **not** show that DESi "understands" Wikipedia, replaces knowledge graphs, or
builds memory. It measures one thing: deterministic epistemic-structure compression and
what it preserves vs. loses.

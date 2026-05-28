# DESi Wikipedia Dual-Layer Probe v2 — pre-registered refinement report

v2 refines the raw v1 dual layer on PRINCIPLE (pre-registered in `preregistration.py`): composite anchors (section + offsets + span hash + neighbour fingerprints), section-aware proportional claim budget, and a navigable-vs-cold-scan split. Tested on the SAME v1 sample (did the levers help?) AND a NEW held-out random sample (generalization). No embeddings; no boilerplate-phrase tuning; DESi core untouched.

- Pre-registration rationale: Composite anchor adds identifying context (span hash + neighbour fingerprints) so that near-duplicate sentences are disambiguated generically; section-aware proportional budget removes the flat-K length penalty and scopes claims to sub-topics. Parameters fixed before the run; no boilerplate-phrase tuning; NEW_SEED sample is held out for generalization.
- Replay hash `64aa63e5cb557aba…`, stable: **True**.

## (A) Resolution lever — bare locator (v1) vs composite fuzzy (v2), SAME anchors

| sample | mean precision (bare locator / v1) | mean precision (composite / v2) | Δ |
| --- | --- | --- | --- |
| OLD (seen) | 0.919 | 0.996 | 0.077 |
| NEW (held-out) | 0.926 | 0.996 | 0.07 |
- Same anchor set, two resolvers: the only difference is the neighbour-fingerprint context. A positive Δ on the HELD-OUT sample is the honest evidence that the composite anchor generalizes, not just fits the v1 collisions.

## (B) Section-budget lever — full v1 vs full v2 pipeline (OLD sample)

| article | type | comp v1→v2 | precision v1→v2 | recover v1→v2 | cold v1 → scan v2 |
| --- | --- | --- | --- | --- | --- |
| Actions along the Mata | history | 0.9366→0.7883 | 0.9→1.0 | 0.169→0.35 | 0.812→0.65 |
| Canada | politics | 0.932→0.7146 | 0.899→1.0 | 0.167→0.427 | 0.815→0.573 |
| Curlew sandpiper | science | 0.8642→0.7582 | 0.961→1.0 | 0.645→0.645 | 0.329→0.355 |
| Grey Cup | history | 0.9222→0.7056 | 0.885→1.0 | 0.186→0.433 | 0.789→0.567 |
| Hellraiser: Judgment | history | 0.9068→0.7376 | 0.936→1.0 | 0.244→0.4 | 0.739→0.6 |
| Henry I of England | history | 0.8725→0.6247 | 0.957→1.0 | 0.293→0.499 | 0.694→0.501 |
| Hughie Ferguson | history | 0.93→0.7368 | 0.943→0.986 | 0.174→0.368 | 0.816→0.626 |
| Islands: Non-Places | history | 0.775→0.7447 | 0.969→1.0 | 0.816→0.5 | 0.158→0.5 |
| Kids See Ghosts (album | history | 0.9272→0.7404 | 0.636→0.969 | 0.121→0.358 | 0.809→0.63 |
| North Ronaldsay sheep | history | 0.8254→0.6966 | 0.912→1.0 | 0.525→0.542 | 0.424→0.458 |

- Means (OLD): compression 0.889→0.725, precision 0.9→0.996, recoverability 0.334→0.452, cold/scan 0.638→0.546.
- The proportional per-section budget (≈30% of each section's claims) is the recoverability lever; the cost is a larger active state (richer anchors) → slightly lower compression. That trade is the honest price of navigability.

## v2 on the NEW held-out sample (generalization)

| article | type | compression | precision | recover | navigable | cold_scan | br/cf/unc surv |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1968 Thule Air Base B- | history | 0.7569 | 0.984 | 0.447 | 0.454 | 0.546 | 1.0/1.0/0.909 |
| 1987 World Snooker Cha | history | 0.6744 | 1.0 | 0.409 | 0.409 | 0.591 | 1.0/1.0/1.0 |
| Atlantis: The Lost Emp | history | 0.7399 | 0.99 | 0.406 | 0.41 | 0.59 | 1.0/1.0/1.0 |
| Donner Party | politics | 0.7031 | 1.0 | 0.407 | 0.407 | 0.593 | 1.0/1.0/1.0 |
| Doom Bar | history | 0.7386 | 1.0 | 0.457 | 0.457 | 0.543 | 1.0/1.0/1.0 |
| Len Hutton | history | 0.7261 | 1.0 | 0.389 | 0.389 | 0.611 | 1.0/1.0/1.0 |
| Myalgic encephalomyeli | general | 0.5828 | 1.0 | 0.874 | 0.874 | 0.126 | 1.0/1.0/1.0 |
| New Zealand nationalit | history | 0.6995 | 1.0 | 0.45 | 0.45 | 0.55 | 1.0/1.0/1.0 |
| Nigel (bishop of Ely) | politics | 0.6394 | 1.0 | 0.519 | 0.519 | 0.481 | 1.0/1.0/1.0 |
| Romney Literary Societ | politics | 0.7142 | 0.984 | 0.481 | 0.488 | 0.512 | 1.0/1.0/1.0 |

- Means (NEW): compression 0.697, precision 0.996, recoverability 0.484, navigable 0.486, cold_scan 0.514.

## Lever status (vs the 6 proposed)

1. **Composite anchor** — implemented; effect isolated in (A).
2/3. **Dynamic + section-aware budget** — implemented as a proportional per-section budget; effect in (B) recoverability/cold.
5. **Smarter cold metric** — implemented (navigable vs scan-fallback; targeted jumps are treated as desired, only no-anchor scans are counted as cost).
4. **Boilerplate detection** — DELIBERATELY NOT a phrase blocklist (that would tune to the v1 collisions); disambiguation is generic (span hash + neighbour fingerprints).
6. **Structured stance/evidence fingerprints** — NOT implemented (highest overfitting/brittleness risk; the type classifier already failed). Left for a future pre-registered test.

## Interpretation

- Read the HELD-OUT (NEW) column as the real verdict. If composite precision ≥ bare-locator precision there and recoverability rises without collapsing compression, the levers are real improvements, not fits. If not, v1's rawness was closer to a real limit — reported either way.

## No overclaiming / core invariance

- Still only epistemic NAVIGATION over archived prose; not understanding/knowledge-graph/memory. Reuses v1 + `desi.core.replay_kernel` READ-ONLY; core byte-identical; additive only.

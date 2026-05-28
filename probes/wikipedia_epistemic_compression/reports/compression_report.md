# DESi Wikipedia Epistemic-Compression Probe — per-article report

Measurement experiment: treat each Wikipedia article as an epistemic STATE SPACE (claims / branches / conflicts / uncertainty / citations / open regions) and measure which structures survive strong, deterministic compression into a compact DESi-style state. No embeddings, no retrieval, no summarization, no DESi-core change. The compressed state keeps the top-K core claims plus the FULL set of branch/conflict/uncertainty markers, then we measure what is lost (anchors not covered, claims beyond budget, and — always — the prose itself).

## Frozen set (reproducible, not curated)

- Seed: **20260528** — rule `random.Random(SEED).sample(sorted(pool), N)`.
- Pool: Category:Featured articles (namespace 0), size 6929, sha256 `940d52ea5e814978…`. Frozen at 2026-05-28T19:17:02Z.
- Replay: metrics are a pure function of the cached text; replay hash `9bc0b6ac2a6d12e3…`, stable across two builds: **True**.

## Per-article measures

| article | type | raw_tok | state_tok | compress | claims (kept) | branch | conflict | uncert | cites | recover | loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Actions along the Matanika | history | 4699 | 387 | 0.9176 | 158 (25) | 0 | 1 | 4 | 73 | 0.265 | 0.735 |
| Canada | politics | 10662 | 640 | 0.94 | 370 (25) | 8 | 9 | 27 | 1013 | 0.221 | 0.779 |
| Curlew sandpiper | science | 3933 | 421 | 0.893 | 65 (25) | 2 | 6 | 20 | 151 | 0.638 | 0.362 |
| Grey Cup | history | 7059 | 522 | 0.9261 | 236 (25) | 3 | 20 | 5 | 240 | 0.346 | 0.654 |
| Hellraiser: Judgment | history | 5279 | 425 | 0.9195 | 171 (25) | 1 | 9 | 13 | 202 | 0.438 | 0.562 |
| Henry I of England | history | 9788 | 695 | 0.929 | 359 (25) | 13 | 23 | 54 | 894 | 0.392 | 0.608 |
| Hughie Ferguson | history | 5160 | 455 | 0.9118 | 182 (25) | 3 | 7 | 0 | 370 | 0.337 | 0.663 |
| Islands: Non-Places | history | 1449 | 317 | 0.7812 | 32 (25) | 1 | 1 | 5 | 98 | 0.791 | 0.209 |
| Kids See Ghosts (album) | history | 4669 | 413 | 0.9115 | 161 (25) | 0 | 3 | 6 | 342 | 0.288 | 0.712 |
| North Ronaldsay sheep | history | 2027 | 369 | 0.818 | 54 (25) | 3 | 0 | 8 | 126 | 0.684 | 0.316 |

## Per-article: preserved vs lost epistemic structure

### Actions along the Matanikau (history)

- Compression 0.9176 (4699→387 tokens). Sections 11, sentences 278, frame-diversity 3.
- **Preserved (existence-level):** branches 0, conflicts 1, uncertainty markers 4 (branches/conflicts/uncertainty kept in full: 1/1/1); citation anchors 73.
- **Lost:** 133 claims beyond the 25-claim budget (claim coverage 0.158); anchor recoverability 0.265 → 0.735 of distinct entity anchors not in the state; ALL prose / implicit context (state holds 0 prose tokens).
- DESi vector: {"anchor_density": 1.288, "contradiction_load": 0.004, "branch_cost": 0.0, "uncertainty_load": 0.014, "citation_support": 0.462, "open_region_ratio": 0.636}.

### Canada (politics)

- Compression 0.94 (10662→640 tokens). Sections 34, sentences 437, frame-diversity 3.
- **Preserved (existence-level):** branches 8, conflicts 9, uncertainty markers 27 (branches/conflicts/uncertainty kept in full: 1/1/1); citation anchors 1013.
- **Lost:** 345 claims beyond the 25-claim budget (claim coverage 0.068); anchor recoverability 0.221 → 0.779 of distinct entity anchors not in the state; ALL prose / implicit context (state holds 0 prose tokens).
- DESi vector: {"anchor_density": 1.854, "contradiction_load": 0.021, "branch_cost": 0.018, "uncertainty_load": 0.062, "citation_support": 2.738, "open_region_ratio": 0.588}.

### Curlew sandpiper (science)

- Compression 0.893 (3933→421 tokens). Sections 14, sentences 172, frame-diversity 3.
- **Preserved (existence-level):** branches 2, conflicts 6, uncertainty markers 20 (branches/conflicts/uncertainty kept in full: 1/1/1); citation anchors 151.
- **Lost:** 40 claims beyond the 25-claim budget (claim coverage 0.385); anchor recoverability 0.638 → 0.362 of distinct entity anchors not in the state; ALL prose / implicit context (state holds 0 prose tokens).
- DESi vector: {"anchor_density": 0.948, "contradiction_load": 0.035, "branch_cost": 0.012, "uncertainty_load": 0.116, "citation_support": 2.323, "open_region_ratio": 0.857}.

### Grey Cup (history)

- Compression 0.9261 (7059→522 tokens). Sections 19, sentences 269, frame-diversity 4.
- **Preserved (existence-level):** branches 3, conflicts 20, uncertainty markers 5 (branches/conflicts/uncertainty kept in full: 1/1/1); citation anchors 240.
- **Lost:** 211 claims beyond the 25-claim budget (claim coverage 0.106); anchor recoverability 0.346 → 0.654 of distinct entity anchors not in the state; ALL prose / implicit context (state holds 0 prose tokens).
- DESi vector: {"anchor_density": 1.803, "contradiction_load": 0.074, "branch_cost": 0.011, "uncertainty_load": 0.019, "citation_support": 1.017, "open_region_ratio": 0.737}.

### Hellraiser: Judgment (history)

- Compression 0.9195 (5279→425 tokens). Sections 12, sentences 221, frame-diversity 3.
- **Preserved (existence-level):** branches 1, conflicts 9, uncertainty markers 13 (branches/conflicts/uncertainty kept in full: 1/1/1); citation anchors 202.
- **Lost:** 146 claims beyond the 25-claim budget (claim coverage 0.146); anchor recoverability 0.438 → 0.562 of distinct entity anchors not in the state; ALL prose / implicit context (state holds 0 prose tokens).
- DESi vector: {"anchor_density": 1.353, "contradiction_load": 0.041, "branch_cost": 0.005, "uncertainty_load": 0.059, "citation_support": 1.181, "open_region_ratio": 0.583}.

### Henry I of England (history)

- Compression 0.929 (9788→695 tokens). Sections 24, sentences 398, frame-diversity 2.
- **Preserved (existence-level):** branches 13, conflicts 23, uncertainty markers 54 (branches/conflicts/uncertainty kept in full: 1/1/1); citation anchors 894.
- **Lost:** 334 claims beyond the 25-claim budget (claim coverage 0.07); anchor recoverability 0.392 → 0.608 of distinct entity anchors not in the state; ALL prose / implicit context (state holds 0 prose tokens).
- DESi vector: {"anchor_density": 1.045, "contradiction_load": 0.058, "branch_cost": 0.033, "uncertainty_load": 0.136, "citation_support": 2.49, "open_region_ratio": 0.625}.

### Hughie Ferguson (history)

- Compression 0.9118 (5160→455 tokens). Sections 15, sentences 212, frame-diversity 3.
- **Preserved (existence-level):** branches 3, conflicts 7, uncertainty markers 0 (branches/conflicts/uncertainty kept in full: 1/1/1); citation anchors 370.
- **Lost:** 157 claims beyond the 25-claim budget (claim coverage 0.137); anchor recoverability 0.337 → 0.663 of distinct entity anchors not in the state; ALL prose / implicit context (state holds 0 prose tokens).
- DESi vector: {"anchor_density": 1.443, "contradiction_load": 0.033, "branch_cost": 0.014, "uncertainty_load": 0.0, "citation_support": 2.033, "open_region_ratio": 0.533}.

### Islands: Non-Places (history)

- Compression 0.7812 (1449→317 tokens). Sections 7, sentences 52, frame-diversity 4.
- **Preserved (existence-level):** branches 1, conflicts 1, uncertainty markers 5 (branches/conflicts/uncertainty kept in full: 1/1/1); citation anchors 98.
- **Lost:** 7 claims beyond the 25-claim budget (claim coverage 0.781); anchor recoverability 0.791 → 0.209 of distinct entity anchors not in the state; ALL prose / implicit context (state holds 0 prose tokens).
- DESi vector: {"anchor_density": 1.654, "contradiction_load": 0.019, "branch_cost": 0.019, "uncertainty_load": 0.096, "citation_support": 3.062, "open_region_ratio": 0.286}.

### Kids See Ghosts (album) (history)

- Compression 0.9115 (4669→413 tokens). Sections 13, sentences 180, frame-diversity 3.
- **Preserved (existence-level):** branches 0, conflicts 3, uncertainty markers 6 (branches/conflicts/uncertainty kept in full: 1/1/1); citation anchors 342.
- **Lost:** 136 claims beyond the 25-claim budget (claim coverage 0.155); anchor recoverability 0.288 → 0.712 of distinct entity anchors not in the state; ALL prose / implicit context (state holds 0 prose tokens).
- DESi vector: {"anchor_density": 2.006, "contradiction_load": 0.017, "branch_cost": 0.0, "uncertainty_load": 0.033, "citation_support": 2.124, "open_region_ratio": 0.538}.

### North Ronaldsay sheep (history)

- Compression 0.818 (2027→369 tokens). Sections 12, sentences 94, frame-diversity 3.
- **Preserved (existence-level):** branches 3, conflicts 0, uncertainty markers 8 (branches/conflicts/uncertainty kept in full: 1/1/1); citation anchors 126.
- **Lost:** 29 claims beyond the 25-claim budget (claim coverage 0.463); anchor recoverability 0.684 → 0.316 of distinct entity anchors not in the state; ALL prose / implicit context (state holds 0 prose tokens).
- DESi vector: {"anchor_density": 1.043, "contradiction_load": 0.0, "branch_cost": 0.032, "uncertainty_load": 0.085, "citation_support": 2.333, "open_region_ratio": 0.583}.

## Core invariance
- Peripheral probe: imports `desi.core.replay_kernel` and `desi.frames` READ-ONLY; adds only new files; DESi core byte-identical.

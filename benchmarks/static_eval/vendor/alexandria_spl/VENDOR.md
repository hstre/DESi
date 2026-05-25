# Vendored: Alexandria Semantic Projection Layer (SPL)

`spl.py` and `spl_gateway.py` are **unmodified copies** of the original SPL from
<https://github.com/hstre/Alexandria-Semantic-Projection-Layer> (MIT License,
Copyright (c) 2026 Steffen Rentschler — see `LICENSE`).

They are vendored here only so the DESi integration is reproducible after the
build container is reclaimed (the external repo is cloned, not packaged). They
are **original SPL code**, not DESi code. The DESi-side glue lives in
`../spl_projection_adapter.py` (clearly marked as the adapter).

Original SPL invariant (spl.py docstring): *"No text fragment may become a
canonical ClaimNode directly. The path is: text → SemanticUnit →
SemanticProjection → ClaimCandidate → (ClaimCandidateConverter) → ClaimNode."*
`spl_gateway.SPLGateway.emit_claim_nodes()` is the only legal candidate→node path.

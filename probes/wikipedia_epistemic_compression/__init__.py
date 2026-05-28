"""DESi Wikipedia Epistemic-Compression Probe (peripheral, additive, no embeddings).

A measurement experiment: treat real Wikipedia articles as an epistemic STATE SPACE
(claims / evidence / conflicts / branches / uncertainties / open regions) and measure
which epistemic structures survive strong, deterministic compression into a compact
DESi-style state. Not a summarizer, not a product.

Adds ONLY new files. Reuses the DESi core READ-ONLY (`desi.core.replay_kernel` for
replay-hashing, `desi.frames.FrameDetector` for per-section frames). No embeddings, no
vector DB, no semantic retrieval, no DESi-core change.
"""

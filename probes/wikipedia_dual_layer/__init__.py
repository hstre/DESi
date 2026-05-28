"""DESi Wikipedia Dual-Layer Retrieval Probe (peripheral, additive, no embeddings).

Two layers:
  * Narrative layer (COLD)  -- the full Wikipedia prose, kept verbatim (archive).
  * DESi state layer (ACTIVE) -- a compact epistemic map (claims / conflicts / branches /
    uncertainties) whose every unit carries a NARRATIVE ANCHOR (section + char offsets +
    a short locator) pointing back into the cold prose.

Research question: NOT "can DESi replace Wikipedia?" but "can DESi work as a compact
epistemic NAVIGATION layer over full prose -- reliably leading back to the relevant
narrative location?" No embeddings, no retrieval engine: only deterministic anchors,
replayable offsets, and lexical locators.

Reuses the previous probe's frozen set + cache + extraction READ-ONLY (same 10 articles,
same seed, same cache). Adds only new files; DESi core untouched.
"""

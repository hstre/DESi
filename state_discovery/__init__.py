"""DESi State Discovery — Prototype 3.

Question under test: can a normal research dialog be automatically lifted into a structured
epistemic state, WITHOUT explicit markers in the chat?

Discovery is deterministic and lexical (no embeddings, no LLM, no semantic similarity). The
extractor uses cue lists (decision verbs, hedge verbs, negation, interrogatives, etc.) to
classify sentences. It has zero knowledge of the ground truth files, which are loaded only
by the evaluator. Three success modes are equally acceptable per the brief: confirmed,
partially confirmed, refuted.
"""

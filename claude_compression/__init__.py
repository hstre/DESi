"""DESi Compression Layer for Claude — minimal context-compression prototype.

Scope LIMITED TO: state extraction, context compression, rehydration. Nothing else.

NOT IMPLEMENTED (out of scope, per the brief):
  Concept Gates, Governance Core, Mutation Layer, Evolution Memory, Agent systems,
  self-improvement, anything beyond compression.

Honest limit of this environment: I CANNOT spin up a second Claude session here to test whether
"Claude in the new chat remains workable." That success criterion requires a real two-session A/B
which is out of scope of a local prototype. What I CAN measure deterministically:
  - real token savings (model2vec tokenizer, identical to the paper-cited counter)
  - whether the compact state preserves the ARCHITECTURE DECISIONS the brief lists, by checking
    each fixture's pre-registered ground-truth markers (not my own extractor's claims)
  - reconstruction sanity (can the rehydrated prompt be parsed back to the same state?)
The "workability" success criterion is reported as `UNTESTED_in_this_env`, honestly.

No claims about AGI / alignment / general problem-solving. This is a context-compression
experiment for LLM-assisted research work, nothing more.
"""

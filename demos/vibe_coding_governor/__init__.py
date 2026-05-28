"""DESi Vibe-Coding Governor demo (peripheral, deterministic, offline).

A minimal demonstration of DESi as an *epistemic build-governor* for iterative,
LLM-generated code changes: it accepts clean in-frame edits, BLOCKS edits that
break explicit governance invariants, and routes architecturally-significant
edits to a SANDBOX -- all decisions replay-hash-chained for bit-reproducibility.

This package adds ONLY new peripheral files. It imports the existing DESi core
(`desi.core.replay_kernel`, `desi.gates.concept_gate`) READ-ONLY and changes no
core component.
"""

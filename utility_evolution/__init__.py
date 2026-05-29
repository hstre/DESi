"""DESi Utility Evolution — peripheral, additive. Optimizes for HUMAN usefulness, not metrics.

This package treats "evolution" as a deterministic, replayable generate-screen-rank process
over a registry of candidate utility improvements (here: the research-tooling direction). It is
honest about scale: it reports the REAL number of candidates evaluated, not a fabricated
2500-loop log. Survivors above a build threshold are actually implemented (see `paper_audit/`);
the rest are specced or discarded WITH reasons. No DESi-core change; replay via the real kernel.
"""

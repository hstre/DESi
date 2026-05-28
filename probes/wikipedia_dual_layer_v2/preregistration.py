"""Pre-registration of the v2 extractor parameters.

These constants are FIXED here, before running v2, and are justified on principle — NOT
derived from v1's observed collisions. In particular: we add NO phrase-specific boilerplate
blocklist (e.g. no special handling of "Retrieved ..."); disambiguation is generic
(span hash + neighbour fingerprints). The per-section budget is proportional, chosen to
remove the flat-budget length penalty, not tuned to any recoverability number.

Honest note: changing parameters AFTER seeing v2 results, or re-running with new values to
raise a metric, would void this pre-registration. The new random sample (NEW_SEED) is the
held-out generalization test.
"""
from __future__ import annotations

# --- anchor (kept identical to v1 where possible, to isolate the effect of the additions) ---
LOCATOR_LEN = 6            # same as v1: the improvement must come from STRUCTURE, not a bigger key
NEIGHBOR_FP_LEN = 4        # content tokens of the previous / next sentence
FP_WEIGHT = 0.5            # weight of each neighbour-fingerprint Jaccard in the fuzzy score
SPAN_HASH_HEX = 8          # length of the span content hash prefix

# --- section-aware proportional claim budget (replaces v1's flat global K=25) ---
SECTION_BUDGET_FRAC = 0.30  # keep ~30% of each section's pure-claim sentences
SECTION_BUDGET_MIN = 2      # ... but at least this many per non-empty section
SECTION_BUDGET_CAP = 20     # ... and at most this many per section

# --- held-out generalization sample ---
NEW_SEED = 20260601         # distinct documented seed for the NEW random sample (vs v1's 20260528)
N = 10

RATIONALE = (
    "Composite anchor adds identifying context (span hash + neighbour fingerprints) so that "
    "near-duplicate sentences are disambiguated generically; section-aware proportional budget "
    "removes the flat-K length penalty and scopes claims to sub-topics. Parameters fixed before "
    "the run; no boilerplate-phrase tuning; NEW_SEED sample is held out for generalization."
)

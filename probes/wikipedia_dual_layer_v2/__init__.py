"""DESi Wikipedia Dual-Layer Retrieval Probe v2 (peripheral, additive, no embeddings).

A PRE-REGISTERED refinement of the v1 dual-layer probe. v1 showed the navigation
architecture is plausible (offset integrity 1.0, locator precision ~0.90) but raw:
weak 6-token locators collided on boilerplate and a flat K=25 claim budget penalized
long articles. v2 addresses these on PRINCIPLE (not by patching the observed failures):

  * composite anchor   -- section path + sentence index + char offsets + span hash +
                          neighbour-sentence fingerprints (more identifying context).
  * section-aware state -- Article -> Sections -> units, with a proportional PER-SECTION
                          claim budget (no global length penalty; sub-topics preserved).
  * smarter cold metric -- separate navigable (targeted jump = desired) from scan-fallback
                          (no anchor = undesired).

All v2 parameters are frozen in `preregistration.py` BEFORE running and are tested on the
SAME v1 sample (did the levers help?) AND a NEW random sample (generalization, not a fit to
the 10 articles whose failures we already saw). No embeddings; DESi core untouched.
"""

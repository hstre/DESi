"""DESi Claude-Layer Probe — peripheral measurement, no new feature engineering.

Question (per the brief): can DESi be installed as a Claude layer that maintains the epistemic
working state and thereby saves tokens on long work processes? Not "DESi saves X%".

Adds ONLY new files. Reads existing per-branch token-pair artifacts READ-ONLY (extracted via
git show into data_inventory/) — does not modify any prior probe. No DESi-core change.
Honest from the start: state-type labels are preserved per source; nothing is averaged
across systems that measure different things without flagging it.
"""

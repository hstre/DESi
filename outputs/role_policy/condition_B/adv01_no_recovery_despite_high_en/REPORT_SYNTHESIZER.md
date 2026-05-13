# DESi Final Synthesis Report

## Trajectory: adv01_no_recovery_despite_high_en

---

## Executive Summary

This trajectory demonstrates a **classification-outcome mismatch** in the bimodal EN threshold system. A single EN event classified as `genuine_transformation` (ENI composite = 0.49) produced zero downstream novelty recovery and was followed by terminal attractor lock. The trajectory is an adversarial probe designed to test this specific failure mode, and findings should not be generalized to natural trajectories.

---

## Supported Findings

*These findings are supported by deterministic metrics AND at least two analyst roles, with no unresolved high-severity objections.*

### Finding 1: Terminal attractor lock on claim C001
- **Evidence**: Monotonic dup_rate increase (0.05 → 0.65), novelty collapse (12 → 0), focus recurrence on C001 across all 6 steps, terminal failure mode declared as ATTRACTOR_LOCK at loop 5.
- **Supporting roles**: ATTRACTOR_DIAGNOSTICIAN (high confidence), TRAJECTORY_ANALYST (observed pattern), deterministic metrics (terminal_failure_mode = ATTRACTOR_LOCK)
- **Objection status**: Objection 3 (confidence downgrade) is MEDIUM severity — upheld. Confidence downgraded to **Medium** with caveat: n=6 steps, probe condition.
- **Status**: ✅ **SUPPORTED** (confidence: Medium)

### Finding 2: EN event at loop 1 produced zero downstream novelty recovery
- **Evidence**: `novel_claims_next = 0` at loop 2, remaining 0 through loop 5. No recovery observed.
- **Supporting roles**: EN_EVENT_ANALYST (zero recovery), TRAJECTORY_ANALYST (EN produced zero novel claims), deterministic metrics (novel_claims_next=0, recovered=False)
- **Objection status**: No high-severity objections to this factual claim.
- **Status**: ✅ **SUPPORTED** (confidence: High)

### Finding 3: The trajectory exhibits a classification-outcome mismatch for the EN event
- **Evidence**: EN classified as `genuine_transformation` (ENI composite = 0.49, eni_novelty = 0.25) but produces zero downstream transformation effect.
- **Supporting roles**: EN_EVENT_ANALYST (identifies mismatch), TRAJECTORY_ANALYST (alternative interpretation), SKEPTICAL_AUDITOR (Objection 1)
- **Objection status**: Objection 1 (HIGH severity) is resolved by reframing — the mismatch is the finding, not the classification. Objection 4 (HIGH severity) is resolved by using "classification-outcome mismatch" label instead of "FALSE RETURN."
- **Status**: ✅ **SUPPORTED** (confidence: High)

---

## Disputed Findings

### Finding 4: The EN event is a "false return"
- **Claim**: EN_EVENT_ANALYST classified the EN as "FALSE RETURN."
- **Dispute**: SKEPTICAL_AUDITOR Objection 4 (HIGH severity) — the analyst substituted their own classification for the metric-based one. The deterministic metrics classify it as `genuine_transformation`. The analyst should not override the metric classification.
- **Resolution**: Replaced with Finding 3 (classification-outcome mismatch). The "FALSE RETURN" label is **rejected** as it overrides deterministic metrics.
- **Status**: ❌ **DISPUTED** — do not use "FALSE RETURN" label

### Finding 5: "Single-EN collapse" is a generalizable pattern
- **Claim**: TRAJECTORY_ANALYST described a "Single-EN collapse" pattern.
- **Dispute**: SKEPTICAL_AUDITOR Objection 2 (MEDIUM severity) — with n=1 EN event, there is no pattern, only an observation. The label implies generalizability.
- **Resolution**: Downgraded to "single EN event observed with subsequent collapse." No pattern inference.
- **Status**: ❌ **DISPUTED** — do not claim pattern; report as single observation

---

## Exploratory Findings

*These findings are not supported by deterministic metrics or sufficient analyst agreement. They require replication.*

### Finding 6: The bimodal EN threshold may misclassify low-novelty EN events
- **Basis**: The probe seed explicitly tests this. The ENI_Novelty of 0.25 is below typical transformation thresholds. The classification as `genuine_transformation` may be a threshold artifact.
- **Limitations**: n=1 EN event, probe condition, single trajectory. Cannot determine if this is systematic or idiosyncratic.
- **Status**: 🔬 **EXPLORATORY** — requires replication with multiple trajectories and varied ENI_Novelty values

### Finding 7: Phase II (FIRST_SATURATION_MODULATION) may be an artifact of under-constrained detection
- **Basis**: Phase II detected at loop 1 spans only 1 loop. SKEPTICAL_AUDITOR Objection 5 (MEDIUM severity) notes insufficient duration for confirmation.
- **Limitations**: Single-loop phase detection is inherently unreliable. The novelty collapse (12→2) may be a step change, not a phase transition.
- **Status**: 🔬 **EXPLORATORY** — requires longer trajectories or multi-loop phase confirmation

---

## Required Revisions

### Revision 1: Confidence downgrade for attractor diagnosis
- **Action**: ATTRACTOR_DIAGNOSTICIAN's "High confidence" downgraded to **Medium**.
- **Reason**: SKEPTICAL_AUDITOR Objection 3 (MEDIUM severity) — n=6 steps, probe condition, only 1 step of confirmed lock.
- **Status**: ✅ **ACCEPTED**

### Revision 2: Remove "FALSE RETURN" classification
- **Action**: EN_EVENT_ANALYST's "FALSE RETURN" label replaced with "classification-outcome mismatch."
- **Reason**: SKEPTICAL_AUDITOR Objection 4 (HIGH severity) — analyst overrode metric classification.
- **Status**: ✅ **ACCEPTED**

### Revision 3: Downgrade "Single-EN collapse" pattern to single observation
- **Action**: TRAJECTORY_ANALYST's pattern label removed. Report as "single EN event observed."
- **Reason**: SKEPTICAL_AUDITOR Objection 2 (MEDIUM severity) — n=1 cannot support pattern inference.
- **Status**: ✅ **ACCEPTED**

### Revision 4: Downgrade overall uncertainty to "High"
- **Action**: TRAJECTORY_ANALYST's "Medium-High" uncertainty upgraded to **High**.
- **Reason**: SKEPTICAL_AUDITOR Objection 7 (MEDIUM severity) — probe condition, n=1 EN, n=6 steps, classification under test.
- **Status**: ✅ **ACCEPTED**

### Revision 5: Note Phase II as unconfirmed

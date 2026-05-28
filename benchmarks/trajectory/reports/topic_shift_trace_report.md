# DESi topic-shift / abrupt-context-switch robustness

Abrupt topic-switch trajectories built by stitching DeepDialogue dialogues from distinct domains (known shift boundaries at the joins; no label tuning). Per turn: lexical topic-continuity / discontinuity + DESi frame. Shift detection compared: (A) raw-transcript novelty proxy vs (B) DESi compact-state discontinuity spikes. Spike rule = trajectory-internal mean+1*std (deterministic). No embeddings, no LLM, no core change.

## Size
- Trajectories: **300** (3 domains each, ~18.0 turns, 2 ground-truth shifts each).

## Compression

| metric | mean | median |
| --- | --- | --- |
| raw transcript tokens | 582.393 | 580.0 |
| DESi state tokens | 176.94 | 174.0 |
| compression ratio | 0.695 | 0.696 |
- **Compression > 90%?** 0/300 (0%) exceed 90% (mean 70%).

## Shift detection: raw proxy (A) vs DESi compact state (B)

| metric | A (raw transcript) | B (DESi state) |
| --- | --- | --- |
| shift precision | 0.238 | 0.102 |
| shift recall | 0.417 | 0.225 |
| shift F1 | 0.292 | 0.138 |
- DESi F1 >= raw-proxy F1 on 143/300 trajectories.

## Topic-shift structure in the compact state

- discontinuity at shift turns 0.984 vs non-shift turns 0.936 (separation only 0.048); the sign is positive on 286/300 trajectories but the MAGNITUDE is negligible -> abrupt shifts do NOT produce a salient discontinuity spike above ordinary within-topic turn-to-turn churn on short chat (both sit near the 0.94-0.98 ceiling).
- recovery after shift (continuity rebuilds next turn): 0.57.
- branch abandonment (old-topic overlap at shift turn, ~0 = cleanly dropped): 0.133.

## Catastrophic / failure analysis

- DESi missed ALL shifts (F1=0): 205/300: ts-0000, ts-0002, ts-0003, ts-0004, ts-0005, ts-0006
- DESi loses continuity (within-segment noisier than the shift): 13/300.
- DESi OUTPERFORMS raw proxy (F1_B > F1_A): 28/300.

## Verdict

**DESi FAILED abrupt topic-switch robustness on this benchmark.**

Per the pre-registered rule ("if it fails badly: document honestly and stop"), this is recorded as a **negative result** and the detector is **NOT** tuned to rescue it.

## Final answers

- **Dataset selected & why:** DeepDialogue-xtts -- loadable English multi-turn dialogues with explicit domains; stitching distinct domains gives abrupt shifts with exact, label-free ground truth (MP2D/WikiDialog were unavailable/script-blocked).
- **Did DESi survive abrupt topic switching?** NO -- shift-detection F1 from the compact state is 0.138, BELOW the raw-transcript proxy (0.292); discontinuity separation between shift and non-shift turns is only 0.048, and DESi misses ALL shifts on 205/300 (68%) trajectories.
- **Did compression remain high?** NO for the >90% target -- mean 70% (only 0/300 = 0% exceed 90%); the stitched chat transcripts are short, so the fixed-size state text does not dominate.
- **Which signals degrade most under shifts?** the lexical discontinuity signal itself: short chatty utterances are lexically dissimilar turn-to-turn EVERYWHERE, so non-shift discontinuity (0.936) nearly equals shift discontinuity (0.984) and the stitch boundary is not salient (13/300 trajectories have within-segment noise rivaling the shift).
- **Does DESi preserve trajectory-state better than raw proxies?** NO on this data -- DESi state F1 0.138 < raw proxy 0.292; DESi only >= raw on 143/300 trajectories.
- **Evidence for genuine state compression vs text summarization?** **Not from this benchmark.** The compact state neither localizes the abrupt shifts (F1 below the raw proxy) nor hits the >90% compression target here, so it provides NO support for the 'genuine trajectory-state preservation' claim on short-utterance chat. (It does not disprove the claim either -- it shows the lexical state is the wrong instrument for low-lexical-coherence chat; see limits.)

## Interpretation (honest)

- This is a **failure case**, reported as such. The earlier DriftBench result (rich, constraint-laden, long transcripts) showed strong compression + preserved drift signal; abrupt-switch chat does NOT reproduce that. The likely cause is the data, not a tuning miss: DeepDialogue turns are short and lexically diverse within a single topic, so a purely **lexical** continuity signal cannot separate a real topic boundary from ordinary turn-to-turn vocabulary churn.
- Honest scope of the claim: DESi's compact state is genuine trajectory-state preservation **where the trajectory signal is lexically expressed** (DriftBench constraints/recovery/branches). It is NOT a general-purpose topic-shift detector for short chat, and we do not claim it is. Per the rule, we **stop here** rather than tune a semantic sensor or move the spike threshold to fit these labels.

## DESi-core invariance
- Peripheral; reads `desi.frames` read-only; core byte-identical.

## Honesty / limits
- Shifts are CONSTRUCTED by stitching (not naturally occurring); ground truth is the stitch boundary. Continuity is deterministic lexical overlap; the raw proxy (A) is a new-token-novelty signal. No embeddings, no LLM, no label tuning (spike rule is trajectory-internal mean+1*std, set before the run). A semantic sensor MIGHT detect these shifts -- but that is explicitly out of scope here, and adding it to chase the labels would violate the no-tuning rule.

# Topic-shift dataset inspection

Goal: find a loadable HF dataset to stress DESi trajectory-state compression under
abrupt topic changes. No faking; every claim below was verified by loading/inspecting.

## Candidates checked

| dataset | loadable? | multi-turn? | topic labels? | abrupt-shift annotations? | notes |
| --- | --- | --- | --- | --- | --- |
| MP2D | NO (0 hits) | - | - | - | not on the HF hub under that name |
| TS-WikiDialog | NO (0 hits) | - | - | - | not on the HF hub under that name |
| `djaym7/wiki_dialog` (WikiDialog) | **NO** | yes | per-passage | no | dataset SCRIPT (`wiki_dialog.py`); "Dataset scripts are no longer supported" under datasets>=4 |
| `xywang1/NaturalConv` | yes | yes | per-dialogue topic | no within-dialogue shifts | Chinese text -> deterministic English lexical/frame signals do not apply cleanly |
| `SALT-Research/DeepDialogue-xtts` (DeepDialogue) | **YES** | yes (conversation list) | **per-dialogue `domain`** | no (but constructible) | English; 2477 dialogues across 20+ domains |

## DeepDialogue schema (selected base)

`load`: `data/dialogues_<model>/<id>.json` (2477 JSON files; audio `.wav` ignored).
Each dialogue JSON:
- `domain`: str (e.g. "art", "cars", "coding", ...)
- `model1`, `model2`, `timestamp`
- `conversation`: list of `{speaker, text}` (multi-turn)

Domain coverage (top): cars 149, books 143, art 137, education 134, coding 118,
cooking 98, celebrities 95, politics 84, events 82, languages 68, social 67,
news 65, podcasts 62, nature 58, technology 52, travel 52, history 51, ... (20+).

## Why DeepDialogue is selected

- **Abrupt topic changes are constructible with KNOWN ground truth:** stitching
  multi-turn dialogues from DIFFERENT domains creates a trajectory whose
  domain-boundary turns are exact, label-free shift points (the MP2D construction
  principle, but from a loadable dataset). No within-dataset shift annotation is
  needed and no labels are tuned.
- **Multi-turn continuity stress:** each segment is a real coherent multi-turn
  dialogue, so within-segment continuity is high and the cross-segment join is a
  hard discontinuity -> clean signal-to-noise for shift detection.
- **English + many domains:** the deterministic lexical-continuity and DESi frame
  signals apply directly; 20+ domains give diverse, well-separated topics.
- NaturalConv (Chinese, one topic per dialogue) and WikiDialog (unloadable script)
  are weaker/blocked for this purpose.

## Construction (deterministic, no label tuning)

Topic-switch trajectories = K=3 dialogues from 3 distinct domains (round-robin over
sorted domains; sequential dialogue indices), each segment capped to the first 6
turns -> ~18-turn trajectories with 2 ground-truth shift boundaries. Fully
reproducible; shift boundaries are the stitch points, not learned labels.

# External-reality challenge

Branch `experiment/desi-external-reality-challenge`.

DESi has only ever been tested against trajectories authored by the
same operator team that built DESi (n=10 adversarial suite, n=20
generalization suite, both hand-designed with knowledge of DESi's
failure modes). The held-out distribution that Paper 0 §11.10 and
§12.3 acknowledged as the missing falsification path is finally
exercised here.

## Source

`source/des_state.json` — verbatim from `https://github.com/hstre/DES.git`.
Real DES program execution state (32 iterations, 9 claims, 35
operations). Authored independent of DESi development. DESi has
never seen these data. See `source/PROVENANCE.md`.

## What the challenge does

DESi's source under `src/desi/` is NOT modified. A translator
(`translator.py`) maps upstream DES state to DESi trajectory schema
in two modes:

- **Conservative** (`cycle_1/`): emit only what upstream DES contains;
  leave all DESi-side metrics at their identity values. Honest.
- **Heuristic** (`cycle_2/`): synthesise `novel_claims`, `dup_rate`,
  and `en_events` via three declared heuristics H1, H2, H3. Output is
  not real DES data; it is a best-effort reconstruction. Flagged
  inline.

Each translation is fed to the unchanged DESi `compute_all` +
`detect_phases`. The reports are recorded.

## Headline finding

**birth(B) = 0** under the strong reading of components D (Failure
Detection) and ΔQ (Measurable Improvement) from Paper 0 §12.1.

DESi's diagnostic output on real DES data is dominated by:

- a cycle-6 detector (`step_coherence`) mislabeling missing data as
  self-contradictory (34/35 steps in conservative mode);
- spurious Phase I + Phase II + Phase V triggers caused by missing-
  field defaults;
- 8 fabricated EN events all labeled "unconfirmed" in heuristic
  mode (DESi diagnosing the translator, not the system).

Under the weak Paper-0-§12.1-as-written reading, birth(B) = 1
still nominally holds (DESi did not crash; some output was returned;
the system "tolerated" the input). But the output is misleading
rather than informative.

Paper 0 §12.3 ("birth is a lower bound, not an endpoint") is the
correct reading. This challenge supplies the empirical evidence
behind it.

## Files

- `source/des_state.json` — upstream DES state (read-only).
- `source/des_prototype_state.json` — upstream DES prototype state.
- `source/PROVENANCE.md` — provenance / non-modification record.
- `translator.py` — DES → DESi schema translator (2 modes).
- `cycle_1/` — conservative translation + DESi probe + evaluation.
- `cycle_2/` — heuristic translation + DESi probe + evaluation.
- `synthesis.md` — verdict + three concrete Paper-0 revisions
  this challenge identifies.

## Reproducing

```
# Conservative mode (honest, impoverished)
python3 experiments/external_reality_challenge/translator.py \
  experiments/external_reality_challenge/source/des_state.json \
  --mode conservative --source-id state \
  --out experiments/external_reality_challenge/cycle_1/des_translated_conservative.json

# Heuristic mode (best-effort, fabricated fields flagged)
python3 experiments/external_reality_challenge/translator.py \
  experiments/external_reality_challenge/source/des_state.json \
  --mode heuristic --source-id state \
  --out experiments/external_reality_challenge/cycle_2/des_translated_heuristic.json

# Probe DESi on each
PYTHONPATH=src python3 experiments/composite_en_label_falsification/probe.py \
  experiments/external_reality_challenge/cycle_1/des_translated_conservative.json
PYTHONPATH=src python3 experiments/composite_en_label_falsification/probe.py \
  experiments/external_reality_challenge/cycle_2/des_translated_heuristic.json
```

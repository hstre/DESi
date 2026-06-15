# Wrong-slice ablation — design + matcher (no runs)

This directory ships the **pre-registered design** and the **strict matcher** for
the wrong-slice ablation. It deliberately does **not** run the experiment: real
runs need a live LLM and the upstream slice-extraction pipeline, neither of
which is in this repo. The runs happen in the operator's live environment; these
files make that run interpretable and non-opportunistic.

- [`PREREGISTRATION.md`](PREREGISTRATION.md) — frozen design: claim under test,
  hypotheses (incl. the claim-shrink condition), four arms, fixed parameters,
  matching gate, primary metric, decision rules, honest power note, scope.
- [`slice_matcher.py`](slice_matcher.py) — **standalone, stdlib-only**. Admits a
  candidate "wrong" slice only if it is indistinguishable from the correct slice
  on token length, claim count, status schema, provenance schema, structure /
  outline (Gliederung), and format — and actually differs in content. The
  load-bearing control: without it the ablation measures length/density/format
  instead of slice correctness.
- [`audit.py`](audit.py) — append-only JSONL audit; insufficiently matched
  candidates are **discarded and audited**, never patched to pass.
- [`result_schema.py`](result_schema.py) — the per-run `RunResult` record +
  validator; the fixed contract between the live harness and the analysis.
- [`analysis.py`](analysis.py) — paired contrasts (exact McNemar) + the
  pre-registered decision rule (H1 / H0-shrink / H2). Returns `insufficient_data`
  on empty input; **no fabrication**.
- [`integration.py`](integration.py) — the single surface the live harness
  calls: `admit_wrong_slice`, `record`, `analyse`, `prereg_hash`.

Tests: [`tests/wrong_slice/`](../../tests/wrong_slice/).

## Use in a live harness

```python
from integration import admit_wrong_slice, record, analyse

# 1) gate + audit a candidate wrong slice (discard on reject; never patch)
ok, report = admit_wrong_slice(correct, candidate, "data/wrong_slice_audit.jsonl",
                               token_count=my_tokenizer, token_tolerance=0)
if not ok:
    continue  # already audited; build another candidate

# 2) run the model on the admitted slice (your harness), then record the run
res = record(experiment_id="ws1", case_id="case3", arm="wrong_permuted",
             repetition=0, seed=42, provider="groq", model_id="llama-3.1-8b",
             decoding={"temperature": 0.0}, fed_slice=candidate, matcher_ok=True,
             no_loop=True, task_completed=True,
             no_severe_role_adoption=True, no_control_failure=True,
             metrics={"drift": 0.12})

# 3) after all runs, apply the pre-registered analysis (delta fixed beforehand)
verdict = analyse(all_results, delta=0.15)
```

The status-stripped (and status-*corrupted*) ablation is **separate** and runs
**after** this one — see `PREREGISTRATION.md` §8.

# Wrong-slice ablation — design + matcher (no runs)

This directory ships the **pre-registered design** and the **strict matcher** for
the wrong-slice ablation. It deliberately does **not** run the experiment: real
runs need a live LLM and the upstream slice-extraction pipeline, neither of
which is in this repo. The runs happen in the operator's live environment; these
files make that run interpretable and non-opportunistic.

- [`PREREGISTRATION.md`](PREREGISTRATION.md) — frozen design: claim under test,
  hypotheses (incl. the claim-shrink condition), arms, fixed parameters,
  matching gate, primary metric, decision rules, honest power note, scope.
- [`slice_matcher.py`](slice_matcher.py) — **standalone, stdlib-only**. Copy it
  into the live harness. It admits a candidate "wrong" slice only if it is
  indistinguishable from the correct slice on token length, claim count, status
  schema, provenance schema, and format — and actually differs in content. This
  is the load-bearing control: without it the ablation measures length/density/
  format instead of slice correctness.

Tests: [`tests/wrong_slice/test_slice_matcher.py`](../../tests/wrong_slice/test_slice_matcher.py).

## Use in a live harness

```python
from slice_matcher import Slice, Claim, match
# build `correct` and a candidate wrong slice from your real state, then:
report = match(correct, candidate, token_count=my_tokenizer, token_tolerance=0)
assert report.ok, report          # disqualify the candidate if it fails
```

The status-stripped (and status-*corrupted*) ablation is **separate** and runs
**after** this one — see `PREREGISTRATION.md` §8.

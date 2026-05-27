# Small-LLM unfolding gate — cross-summary

A small cheap LLM (Granite 4.1-8b) decides only UNFOLD / DO_NOT_UNFOLD / UNCERTAIN on the ambiguous residue; it never emits a verdict. DeepSeek predictions reused from the residual run so A/B/C are identical and the only new variable is the gate. Policies A matched ceiling / B deterministic unfolding / C residual lexical / D LLM-gate. Core untouched.

## Accuracy by policy

| dataset | A matched | B unfolding | C residual | D LLM-gate | escalated | gate decisions | gate $ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tals/vitaminc | 0.768 | 0.73 | 0.72 | 0.72 | 45/100 | {'UNFOLD': 18, 'DO_NOT_UNFOLD': 27} | $0.000831 |
| pietrolesci/nli_fever | 0.58 | 0.54 | 0.54 | 0.54 | 10/100 | {'UNFOLD': 7, 'DO_NOT_UNFOLD': 3} | $0.000172 |

| dataset | overcommit B->D | overabst B->D | gate net vs B | gate net vs C | parse fails | latency |
| --- | --- | --- | --- | --- | --- | --- |
| tals/vitaminc | 0.463 -> 0.488 | 0.119 -> 0.102 | -1 | +0 | 0 | 17.76s |
| pietrolesci/nli_fever | 0.269 -> 0.269 | 0.486 -> 0.486 | +0 | +0 | 0 | 4.05s |

## Final answers

- **Does small-LLM unfolding help?** tals/vitaminc: D 0.72 vs B 0.73 (-0.010), gate net vs B -1; pietrolesci/nli_fever: D 0.54 vs B 0.54 (+0.000), gate net vs B +0. NO -- the gate is not net-positive vs deterministic unfolding.
- **Does it beat deterministic unfolding (B)?** NO -- it does not consistently beat B. It ties the residual lexical escalation (C) (net +0).
- **Does it approach the matched-prompt ceiling (A)?** gap to ceiling tals/vitaminc: +0.048; pietrolesci/nli_fever: +0.040. No -- the matched-prompt family remains clearly above the gate.
- **Is the added cost justified?** gate cost tals/vitaminc: $0.000831 for 45 calls, 17.76s, net -1; pietrolesci/nli_fever: $0.000172 for 10 calls, 4.05s, net +0. The accuracy did not improve, so the added LLM cost/latency is NOT justified.
- **Did DESi-core remain invariant?** YES -- core byte-identical, replay 1.0, governance independent, mutation rejected on every run; the gate is a peripheral routing aid only.

## Interpretation (per study rule)

- The small-LLM gate does NOT help. Per the study rule, this routing line is STOPPED: no further patching. The unfold/no-unfold decision on this residue is not reliably improved by a small LLM here; the matched-prompt family remains the ceiling. No truthfulness claim; DESi did not solve NLI; DESi-core stayed invariant throughout.

## Honesty / limits

- N=100/dataset; DeepSeek preds reused (A/B/C identical to the residual run); one gate call per escalated item, no retries/voting/CoT; gate emits only the 3 routing decisions. No core/ontology change; key in-process; outputs secret-scanned.

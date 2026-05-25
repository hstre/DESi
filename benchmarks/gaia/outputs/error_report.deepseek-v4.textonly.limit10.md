# GAIA error analysis — submission.validation.deepseek-v4.textonly.limit10.jsonl

- Dataset: `gaia-benchmark/GAIA` [2023_all/validation]
- Tasks scored: **10**
- Accuracy overall: **1/10 = 10.0%**
- Accuracy text-only: **1/9 = 11.1%**
- UNKNOWN/empty answers: **5**
- Suspected reasoning-truncation: **2**
- Suspected web/search/tools needed: **5**

## By error class

| class | count |
| --- | --- |
| correct | 1 |
| attachment_skipped | 1 |
| backend_error | 0 |
| reasoning_truncated | 2 |
| needs_web_search_or_tools | 5 |
| empty_or_unknown | 0 |
| wrong_answer | 1 |
| unknown_failure | 0 |

## By level

| level | correct | total | accuracy |
| --- | --- | --- | --- |
| 1 | 0 | 3 | 0.0% |
| 2 | 1 | 7 | 14.3% |

## Per-task

| task_id | L | class | correct | empty/UNK | req_att | model_answer | gold | finish_reason | question |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| c61d22de | 2 | reasoning_truncated | ✗ | yes | no | (empty) | egalitarian | n/a (not captured) | A paper about AI regulation that was originally submitted to arXiv.or… |
| 17b5a6a3 | 2 | needs_web_search_or_tools | ✗ | no | no | 33062, 33149 | 34689 | n/a (not captured) | I’m researching species that became invasive after people who kept th… |
| 04a04a9b | 2 | needs_web_search_or_tools | ✗ | yes | no | UNKNOWN | 41 | n/a (not captured) | If we assume all articles published by Nature in 2020 (articles, only… |
| 14569e28 | 2 | reasoning_truncated | ✗ | yes | no | (empty) | backtick | n/a (not captured) | In Unlambda, what exact charcter or text needs to be added to correct… |
| e1fc63a2 | 1 | needs_web_search_or_tools | ✗ | no | no | 17000 | 17 | n/a (not captured) | If Eliud Kipchoge could maintain his record-making marathon pace inde… |
| 32102e3e | 2 | attachment_skipped | ✗ | yes | yes | (empty) | Time-Parking 2: Parallel… | n/a (not captured) | The attached spreadsheet shows the inventory for a movie and video ga… |
| 8e867cd7 | 1 | needs_web_search_or_tools | ✗ | no | no | 2 | 3 | n/a (not captured) | How many studio albums were published by Mercedes Sosa between 2000 a… |
| 3627a8be | 2 | correct | ✓ | no | no | 142 | 142 | n/a (not captured) | The object in the British Museum's collection with a museum number of… |
| 7619a514 | 2 | needs_web_search_or_tools | ✗ | yes | no | UNKNOWN | 04/15/18 | n/a (not captured) | According to github, when was Regression added to the oldest closed n… |
| ec09fa32 | 1 | wrong_answer | ✗ | no | no | 37 | 3 | n/a (not captured) | Here's a fun riddle that I think you'll enjoy. You have been selected… |

> Classes are heuristic. `reasoning_truncated` is inferred from an empty answer with no backend error (the reasoning model emitted no content); `needs_web_search_or_tools` is inferred from external-lookup markers in the question. `finish_reason` is only shown when the run captured it.

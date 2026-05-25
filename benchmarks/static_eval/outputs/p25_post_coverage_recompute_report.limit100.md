# P25 post-coverage recompute / architecture re-audit (limit 100, offline)

Re-runs the P21 routing / P22 recall / P23 coverage logic on the P24-repaired claim graph (question-grounded rule extraction + SPL projection; no model calls). Compares OLD (sparse P12 graph) vs NEW (repaired). Claim coverage != truthfulness — this checks whether P24 expanded visibility or just inflated.

## A) Claim coverage

| metric | OLD | NEW |
| --- | --- | --- |
| total atomic claims | 57 | 107 |
| claim-less answers | 76 | 31 |
| substantive claim-less | 12 | 0 |
| logical-content-without-claim | 8 | 0 |

## B) Folding / routing (P21)

| class | OLD | NEW |
| --- | --- | --- |
| folded | 75 | 31 |
| ESCALATE | 6 | 39 |
| LOG_ONLY | 3 | 0 |
| DISCARD | 16 | 30 |

## C) DBA escalation / compute

- escalation-eligible (ESCALATE): **6 -> 39**.
- NEW escalation-eligible cases (added by repair): **33** (tqa-0002, tqa-0008, tqa-0009, tqa-0010, tqa-0013, tqa-0016, tqa-0021, tqa-0022, tqa-0024, tqa-0028, tqa-0030, tqa-0032, tqa-0037, tqa-0041, tqa-0042, tqa-0043, tqa-0044, tqa-0045, tqa-0046, tqa-0047, tqa-0049, tqa-0050, tqa-0052, tqa-0058, tqa-0069, tqa-0074, tqa-0081, tqa-0082, tqa-0083, tqa-0086, tqa-0091, tqa-0092, tqa-0093).
- additional second-builder calls these would require: **33** (total 39/100 vs always-dual 100/100).
- of the NEW escalation-eligible, how many have a persisted Gβ to actually run governance offline: **0** — the rest would need a Granite re-run (NOT done here). So the 'how many semantics would re-close' for new cases is PENDING a second builder; not claimed.

## D) Recall (P22 risk flags)

- non-escalated cases carrying >=1 risk flag: **36/94 -> 30/61**.
| risk class | OLD | NEW |
| --- | --- | --- |
| low_confidence_unresolved | 30 | 14 |
| missed_reconstruction_risk | 6 | 0 |
| missed_logical_risk | 7 | 0 |
| underspecified_single_claim | 3 | 30 |
| missed_semantic_overlap | 3 | 7 |
| hidden_polarity_risk | 0 | 0 |

## Newly-visible cases

- 45 answers that were claim-less now carry claims and are therefore visible to SPL / meaning-space / governance / DBA. The substantive-claim-less blind spot dropped 12 -> 0 and logical-content-without-claim 8 -> 0.

## Did P24 expand the epistemic field, or just add claims?

- **Expanded the field.** Previously-invisible answers (76-31 fewer claim-less) are now present in the claim space the whole pipeline operates on — that is genuine visibility, not just a bigger number. The escalation predicate now SEES logically-loaded / multi-part answers it could not before.
- **But the new claims are crude.** They are rule-grounded (question-topic subject, generic predicate); they make assertions VISIBLE, they do not improve answer quality or truth. Several escalations they create (negated yes/no, conjunction splits) are real epistemic structure, but a few may be low-value.

## New risks from the repair (honest — fuller AND noisier)

- **Escalation inflation:** ESCALATE jumped 6 -> 39. P21's earlier ~94% compute saving was PARTLY an artifact of empty extraction (76% of answers had no claims to escalate); with coverage repaired, true escalation demand is ~39%. The selectivity was overstated before.
- **Crude claims cause FALSE escalation:** the rule extractor splits a single factual answer into several 'includes' claims (e.g. a city/state/park location -> 3 claims) -> >=2 -> ESCALATE, even though it is one simple fact. Some of the 33 new escalations are this inflation, not real divergence risk.
- **Recall risk transformed, not removed:** missed_reconstruction_risk 6 -> 0 and missed_logical_risk 7 -> 0 (good — those answers now carry claims), BUT underspecified_single_claim 3 -> 30 (the fragment-grounding path produces many single crude claims). The tail shifted from 'claim-less' to 'single crude claim'.

## Is folding more sensible now? compute? recall?

- **Folding:** ESCALATE 6 -> 39; folded 75 -> 31. The escalation set now reflects real claim structure rather than an artefact of empty extraction.
- **Compute:** second-builder demand rises sharply to 39/100 (still below always-dual 100/100, but ~6x the optimized P21). It does NOT explode to 100, but the prior selectivity was partly illusory; with full coverage the predicate is too permissive and needs recalibration (much of the jump is crude-claim inflation).
- **Recall:** risk-flagged non-escalated 36 -> 30; low_confidence_unresolved 30 -> 14; missed_reconstruction_risk 6 -> 0. The coverage-driven recall risks (claim-less / under-extracted) shrink because those answers now carry claims; the residual recall risk is more about low confidence than about missing claims.

## Recommendation on P21 recalibration

- The repair shifts ESCALATE to 39/100. If that is above the cross-run budget, recalibrate the claim-structural predicate (e.g. require >=2 claims AND a logical-risk token, or de-duplicate the rule-grounded conjunction splits which inflate claim counts).
- Crucially, re-run the REAL second builder (Granite) on the NEW escalation-eligible cases before trusting the new DBA outcomes — the governed-outcome recompute for new cases is PENDING a key.

## Honesty / limits

- The repaired claim graph uses the OFFLINE rule extractor (no model), so the NEW claims are coarse visibility claims; a model extractor with the improved prompt would produce better triples (needs a key).
- New escalation-eligible cases cannot be governed offline (no Gβ for them) — so 'how many semantics would re-close' is NOT claimed here.
- More claims is NOT more truth. This recompute measures visibility / routing / recall on the new claim space, nothing about correctness.
- No API calls, no new model/score/judge/intervention.

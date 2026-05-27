# Gold-label & task-underdetermination audit — candidates

**Audit-prep only.** Purely mechanical extraction from captured run artifacts (`re_<dataset>.json`): no model calls, no judgment, no relabeling, no change to prompts / routing / evaluator. Each case is a item where the DeepSeek prediction disagrees with the benchmark gold label under one or more of the three FIXED prompt families (baseline / evidence-strict / entailment-direct). The point is to let a human decide whether the LABEL is clean before any further solver fixing.

Mechanical flags (NOT verdicts): *consistent disagreement* = every answered prompt family disagrees with gold; *calibrated-prompt still disagrees* = the family specifically calibrated to fix that error mode (evidence-strict for gold-NEI over-commitment, entailment-direct for gold-committed over-abstention) still disagrees -- i.e. prompt calibration did not rescue the gold.

## Summary (mechanical counts)

| dataset | items | error candidates | gold_NEI_model_commits | gold_committed_model_NEI | direction_flip | consistent disagreement | calibrated still disagrees |
| --- | --- | --- | --- | --- | --- | --- | --- |
| vitaminc | 100 | 44 | 30 | 13 | 1 | 10 | 16 |
| nli_fever | 100 | 56 | 12 | 42 | 2 | 33 | 39 |

Total error candidates across datasets: **100**; of these, **43** are consistent disagreements (all prompts wrong vs gold) and **55** survive their calibrated prompt -- the strongest label-suspicion candidates.

## Data-quality / orientation observations (mechanical)

Field lengths and empty fields per dataset (claim = the field mapped from the dataset's claim/hypothesis column; evidence = the evidence/premise column):

| dataset | median claim len | median evidence len | claim > 2x evidence | empty claim | empty evidence |
| --- | --- | --- | --- | --- | --- |
| vitaminc | 86 | 176 | 0 | 0 | 0 |
| nli_fever | 237 | 42 | 87 | 8 | 0 |

> MECHANICAL FLAG (for human verification, NOT auto-corrected): where the **claim** field is systematically much longer than the **evidence** field, the dataset's premise/hypothesis columns may be oriented opposite to the verify-task assumption ("does EVIDENCE support CLAIM"). Feeding a short evidence against a long multi-fact claim would mechanically push the solver toward NEI -- a candidate LABEL_MAPPING_ARTIFACT that a human should confirm before any solver fixing. Empty claim/evidence fields are also flagged as data artifacts.

## Audit taxonomy (human-assigned only)

- **MODEL_CLEARLY_WRONG** — the gold label is right; the model is simply wrong
- **GOLD_LABEL_PLAUSIBLE** — gold defensible, model defensible too, but gold is fine
- **GOLD_LABEL_QUESTIONABLE** — the gold label looks wrong / hard to justify
- **UNDERDETERMINED** — the evidence does not determine S/R; NEI is defensible
- **PARTIAL_SUPPORT_ONLY** — evidence partially supports; gold treats partial as full
- **REQUIRES_OUTSIDE_KNOWLEDGE** — gold needs world knowledge beyond the evidence
- **BENCHMARK_CONVENTION** — gold follows a dataset convention, not pure entailment
- **AMBIGUOUS_PARAPHRASE** — wording mismatch makes the relation ambiguous
- **LABEL_MAPPING_ARTIFACT** — label normalization/mapping artifact, not content

## Top candidates (ranked by mechanical suspicion; grouped by error type)

Fill `human_audit_label` from the taxonomy in `goldlabel_audit_annotations.jsonl` (template generated alongside).

### gold = NOT_ENOUGH_INFO, model committed (SUPPORTS/REFUTES) — 7 of top 20

#### `vitaminc:vitaminc-0042`
- **gold**: NOT_ENOUGH_INFO | **preds (baseline/evidence-strict/entailment-direct)**: REFUTES/REFUTES/REFUTES
- **changed across prompts**: False | **consistent disagreement**: True | **calibrated (evidence_strict) still disagrees**: True
- **claim**: As of 19 March , less than 230,000 confirmed cases have been reported in 150 countries , resulting in less than 9,000 deaths .
- **evidence**: As of 19 March , more than 223,000 cases of COVID-19 have been reported in over 150 countries and territories , resulting in more than 9,100 deaths and 85,000 recoveries .
- **human_audit_label**: ______  | **comment**: ______ | **confidence (0-1)**: ____

#### `vitaminc:vitaminc-0064`
- **gold**: NOT_ENOUGH_INFO | **preds (baseline/evidence-strict/entailment-direct)**: SUPPORTS/SUPPORTS/SUPPORTS
- **changed across prompts**: False | **consistent disagreement**: True | **calibrated (evidence_strict) still disagrees**: True
- **claim**: Over 184 countries and territories had reported less than 274,000 COVID-19 cases by March 20 , 2020 .
- **evidence**: As of 20 March , more than 272,000 cases of COVID-19 have been reported in over 184 countries and territories , resulting in more than 11,300 deaths and 90,000 recoveries .
- **human_audit_label**: ______  | **comment**: ______ | **confidence (0-1)**: ____

#### `vitaminc:vitaminc-0069`
- **gold**: NOT_ENOUGH_INFO | **preds (baseline/evidence-strict/entailment-direct)**: SUPPORTS/SUPPORTS/SUPPORTS
- **changed across prompts**: False | **consistent disagreement**: True | **calibrated (evidence_strict) still disagrees**: True
- **claim**: Come Away with Me sold approximately 27 million copies worldwide .
- **evidence**: Worldwide , as of October 2016 the album has sold more than 27 million copies .
- **human_audit_label**: ______  | **comment**: ______ | **confidence (0-1)**: ____

#### `vitaminc:vitaminc-0092`
- **gold**: NOT_ENOUGH_INFO | **preds (baseline/evidence-strict/entailment-direct)**: SUPPORTS/SUPPORTS/SUPPORTS
- **changed across prompts**: False | **consistent disagreement**: True | **calibrated (evidence_strict) still disagrees**: True
- **claim**: As of March 22 , 2020 there were under 321,000 coronavirus cases , less than 13,600 deaths and under 96,000 recoveries reported worldwide .
- **evidence**: As of 22 March , more than 315,000 cases of COVID-19 have been reported in over 180 countries and territories , resulting in more than 13,500 deaths and 95,000 recoveries .
- **human_audit_label**: ______  | **comment**: ______ | **confidence (0-1)**: ____

#### `vitaminc:vitaminc-0096`
- **gold**: NOT_ENOUGH_INFO | **preds (baseline/evidence-strict/entailment-direct)**: SUPPORTS/SUPPORTS/SUPPORTS
- **changed across prompts**: False | **consistent disagreement**: True | **calibrated (evidence_strict) still disagrees**: True
- **claim**: More than 317,000 cases of COVID-19 have been confirmed .
- **evidence**: As of 22 March , more than 318,000 cases of COVID-19 have been reported in over 188 countries and territories , resulting in more than 13,600 deaths and 96,000 recoveries .
- **human_audit_label**: ______  | **comment**: ______ | **confidence (0-1)**: ____

#### `nli_fever:nli_fever-0003`
- **gold**: NOT_ENOUGH_INFO | **preds (baseline/evidence-strict/entailment-direct)**: REFUTES/REFUTES/REFUTES
- **changed across prompts**: False | **consistent disagreement**: True | **calibrated (evidence_strict) still disagrees**: True
- **claim**: Anne Rice . Born in New Orleans , Rice spent much of her early life there before moving to Texas , and later to San Francisco . Route 495 is a 3.45 mi freeway in Hudson County , New Jersey , in the United States that connects the New Jersey Turnpike ( Interstate 95 , I-95 ) at exits 16E and 17 in Secaucus to New York State Route 495 ( NY 495 ) inside the Lincoln Tunnel in Weehawken , providing access to Midtown Manhattan .
- **evidence**: Anne Rice was born in New Jersey.
- **human_audit_label**: ______  | **comment**: ______ | **confidence (0-1)**: ____

#### `nli_fever:nli_fever-0011`
- **gold**: NOT_ENOUGH_INFO | **preds (baseline/evidence-strict/entailment-direct)**: REFUTES/REFUTES/REFUTES
- **changed across prompts**: False | **consistent disagreement**: True | **calibrated (evidence_strict) still disagrees**: True
- **claim**: House ( also called House , M.D. ) is an American television medical drama that originally ran on the Fox network for eight seasons , from November 16 , 2004 to May 21 , 2012 .
- **evidence**: House is a sitcom.
- **human_audit_label**: ______  | **comment**: ______ | **confidence (0-1)**: ____

### gold = SUPPORTS/REFUTES, model abstained (NEI) — 13 of top 20

#### `vitaminc:vitaminc-0041`
- **gold**: SUPPORTS | **preds (baseline/evidence-strict/entailment-direct)**: REFUTES/NOT_ENOUGH_INFO/REFUTES
- **changed across prompts**: True | **consistent disagreement**: True | **calibrated (entailment_direct) still disagrees**: True
- **claim**: As of 19 March , more than 220,000 confirmed cases have been reported in 150 countries , resulting in more than 9,000 deaths .
- **evidence**: As of 19 March , more than 220,000 cases of COVID-19 have been reported in over 150 countries and territories , resulting in more than 8,900 deaths and 85,000 recoveries .
- **human_audit_label**: ______  | **comment**: ______ | **confidence (0-1)**: ____

#### `vitaminc:vitaminc-0044`
- **gold**: REFUTES | **preds (baseline/evidence-strict/entailment-direct)**: NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO
- **changed across prompts**: False | **consistent disagreement**: True | **calibrated (entailment_direct) still disagrees**: True
- **claim**: COVID-19 cases as of March 19 , 2020 were less than 225,500 .
- **evidence**: As of 19 March , more than 225,000 cases of COVID-19 have been reported in over 150 countries and territories , resulting in more than 9,200 deaths and 85,000 recoveries .
- **human_audit_label**: ______  | **comment**: ______ | **confidence (0-1)**: ____

#### `vitaminc:vitaminc-0070`
- **gold**: REFUTES | **preds (baseline/evidence-strict/entailment-direct)**: SUPPORTS/NOT_ENOUGH_INFO/SUPPORTS
- **changed across prompts**: True | **consistent disagreement**: True | **calibrated (entailment_direct) still disagrees**: True
- **claim**: Come Away with Me has sold more than 27 million copies worldwide as of October 2016 .
- **evidence**: As of 2016 , the album has sold approximately 27 million copies worldwide .
- **human_audit_label**: ______  | **comment**: ______ | **confidence (0-1)**: ____

#### `vitaminc:vitaminc-0074`
- **gold**: REFUTES | **preds (baseline/evidence-strict/entailment-direct)**: SUPPORTS/NOT_ENOUGH_INFO/SUPPORTS
- **changed across prompts**: True | **consistent disagreement**: True | **calibrated (entailment_direct) still disagrees**: True
- **claim**: More than 90,000 recoveries from coronavirus had been reported by 21 March .
- **evidence**: As of 21 March , more than 275,000 cases of COVID-19 have been reported in over 185 countries and territories , resulting in more than 11,300 deaths and 90,000 recoveries .
- **human_audit_label**: ______  | **comment**: ______ | **confidence (0-1)**: ____

#### `nli_fever:nli_fever-0002`
- **gold**: SUPPORTS | **preds (baseline/evidence-strict/entailment-direct)**: NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO
- **changed across prompts**: False | **consistent disagreement**: True | **calibrated (entailment_direct) still disagrees**: True
- **claim**: Soul Food is a 1997 American comedy-drama film produced by Kenneth `` Babyface '' Edmonds , Tracey Edmonds and Robert Teitel and released by Fox 2000 Pictures .
- **evidence**: Fox 2000 Pictures released the film Soul Food.
- **human_audit_label**: ______  | **comment**: ______ | **confidence (0-1)**: ____

#### `nli_fever:nli_fever-0006`
- **gold**: SUPPORTS | **preds (baseline/evidence-strict/entailment-direct)**: NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO
- **changed across prompts**: False | **consistent disagreement**: True | **calibrated (entailment_direct) still disagrees**: True
- **claim**: Mogadishu ( [ ˌmɔːɡəˈdiːʃuː ] Muqdisho [ mʉqdɪʃɔ ] ; مقديشو [ maqadiːʃuː ] ) , known locally as Hamar , is the capital and most populous city of Somalia . As Somalia 's capital city , many important national institutions are based in Mogadishu .
- **evidence**: There is a capital called Mogadishu.
- **human_audit_label**: ______  | **comment**: ______ | **confidence (0-1)**: ____

#### `nli_fever:nli_fever-0014`
- **gold**: SUPPORTS | **preds (baseline/evidence-strict/entailment-direct)**: NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO
- **changed across prompts**: False | **consistent disagreement**: True | **calibrated (entailment_direct) still disagrees**: True
- **claim**: Carrie Anne Mathison , played by actress Claire Danes , is a fictional character and the protagonist of the American television drama/thriller series Homeland on Showtime , created by Alex Gansa and Howard Gordon . Homeland (TV series) . The series stars Claire Danes as Carrie Mathison , a Central Intelligence Agency officer with bipolar disorder , and Damian Lewis as Nicholas Brody , a U.S. Marine Corps Scout Sniper . Nicholas Brody . Nicholas `` Nick '' Brody , played by actor Damian Lewis , is a fictional character on the American television series Homeland on Showtime , created by Alex Gansa and Howard Gordon .
- **evidence**: Nicholas Brody is a character on Homeland.
- **human_audit_label**: ______  | **comment**: ______ | **confidence (0-1)**: ____

#### `nli_fever:nli_fever-0022`
- **gold**: SUPPORTS | **preds (baseline/evidence-strict/entailment-direct)**: NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO
- **changed across prompts**: False | **consistent disagreement**: True | **calibrated (entailment_direct) still disagrees**: True
- **claim**: Edgar Howard Wright ( born 18 April 1974 ) is an English director , screenwriter , producer , and actor . He is best known for his comedic Three Flavours Cornetto film trilogy consisting of Shaun of the Dead ( 2004 ) , Hot Fuzz ( 2007 ) , and The World 's End ( 2013 ) , made with recurrent collaborators Simon Pegg , Nira Park and Nick Frost . He also collaborated with them as the director of the television series Spaced . He also co-wrote , produced and directed the 2010 film Scott Pilgrim vs. the World . Along with his friends Joe Cornish and Steven Moffat , he co-wrote Steven Spielberg 's The Adventures of Tintin : The Secret of the Unicorn .
- **evidence**: Edgar Wright is a person.
- **human_audit_label**: ______  | **comment**: ______ | **confidence (0-1)**: ____

#### `nli_fever:nli_fever-0023`
- **gold**: SUPPORTS | **preds (baseline/evidence-strict/entailment-direct)**: NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO
- **changed across prompts**: False | **consistent disagreement**: True | **calibrated (entailment_direct) still disagrees**: True
- **claim**: Dorothy Ann Willis Richards ( September 1 , 1933 -- September 13 , 2006 ) was an American politician and the 45th Governor of Texas from 1991 to 1995 . A Democrat , she first came to national attention as the state treasurer of Texas , when she delivered the keynote address at the 1988 Democratic National Convention . Richards served as the 45th Governor of Texas from 1991 to 1995 and was defeated for re-election in 1994 by George W. Bush . Richards was the second female governor of Texas , and was frequently noted in the media for her outspoken feminism and her one-liners . Ann Richards ( October 1 , 1935 -- April 1 , 1982 ) was an American jazz singer and the wife of pianist Stan Kenton .
- **evidence**: Ann Richards was professionally involved in politics.
- **human_audit_label**: ______  | **comment**: ______ | **confidence (0-1)**: ____

#### `nli_fever:nli_fever-0024`
- **gold**: SUPPORTS | **preds (baseline/evidence-strict/entailment-direct)**: NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO
- **changed across prompts**: False | **consistent disagreement**: True | **calibrated (entailment_direct) still disagrees**: True
- **claim**: Drake Bell . Bell released an EP in 2011 called A Reminder independently .
- **evidence**: Drake Bell put out an EP.
- **human_audit_label**: ______  | **comment**: ______ | **confidence (0-1)**: ____

#### `nli_fever:nli_fever-0031`
- **gold**: REFUTES | **preds (baseline/evidence-strict/entailment-direct)**: SUPPORTS/NOT_ENOUGH_INFO/SUPPORTS
- **changed across prompts**: True | **consistent disagreement**: True | **calibrated (entailment_direct) still disagrees**: True
- **claim**: 
- **evidence**: Hot Right Now is mistakenly attributed to DJ Fresh.
- **MECHANICAL FLAG**: empty claim/evidence field (data/mapping artifact)
- **human_audit_label**: ______  | **comment**: ______ | **confidence (0-1)**: ____

#### `nli_fever:nli_fever-0033`
- **gold**: REFUTES | **preds (baseline/evidence-strict/entailment-direct)**: NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO
- **changed across prompts**: False | **consistent disagreement**: True | **calibrated (entailment_direct) still disagrees**: True
- **claim**: 
- **evidence**: Giada at Home was only available on DVD.
- **MECHANICAL FLAG**: empty claim/evidence field (data/mapping artifact)
- **human_audit_label**: ______  | **comment**: ______ | **confidence (0-1)**: ____

#### `nli_fever:nli_fever-0040`
- **gold**: SUPPORTS | **preds (baseline/evidence-strict/entailment-direct)**: NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO
- **changed across prompts**: False | **consistent disagreement**: True | **calibrated (entailment_direct) still disagrees**: True
- **claim**: Big Brother 2017 , also known as Big Brother 18 , is the upcoming eighteenth series of the British reality television series Big Brother , hosted by Emma Willis and narrated by Marcus Bentley . Marcus Morgan Bentley ( born 4 October 1967 ) is a British actor , broadcaster and voice-over artist . Bentley is most famous for narrating the United Kingdom 's version of the Dutch reality television programme Big Brother since its inception in 2000 . He also did other continuity announcements for Channel 4 until he left in July 2011 to continue narrating the revived Big Brother on Channel 5 . Bentley 's voice-over work and Geordie accent has led to him becoming one of Britain 's most recognised voices .
- **evidence**: Marcus Bentley is a broadcaster.
- **human_audit_label**: ______  | **comment**: ______ | **confidence (0-1)**: ____

## How to annotate

1. For each `case_id`, read claim + evidence + gold + the three predictions.
2. Assign ONE taxonomy label in `goldlabel_audit_annotations.jsonl` (`human_audit_label`), add a short `comment`, and a `confidence` 0-1.
3. Re-run `python goldlabel_audit.py --score` AFTER annotating to compute adjusted/clean-label accuracy (it refuses to score until annotations exist).

## Honesty / limits

- Mechanical extraction only; no automatic judgment; gold labels are NOT reinterpreted here. Predictions are the captured DeepSeek outputs (mildly non-deterministic across runs). Claim/evidence are public dataset text. No core, prompt, routing, or evaluator change.

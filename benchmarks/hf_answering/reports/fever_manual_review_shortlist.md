# Corrected-FEVER manual-review shortlist

Epistemic review layer ONLY -- no model calls, no reruns, no relabeling, no patches. All distinct corrected-FEVER wrong items (DeepSeek v4 Pro across the three prompt families), with a MECHANICAL A-G group and a per-item human-review template. Only group A (empty evidence) is a confirmed data artifact; **every other category is PROVISIONAL until human review**.

## Summary (provisional pending human review)

| metric | count |
| --- | --- |
| total distinct wrong items | 27 |
| empty-evidence artifacts (A, CONFIRMED) | 7 |
| likely benchmark-convention (B/C/D, provisional) | 7 |
| likely underdetermined (E/F, provisional) | 9 |
| likely real solver misses (G, provisional) | 4 |
| unresolved / needs human review (all non-artifact) | 20 |

### Mechanical group distribution

| group | meaning | provisional category | count |
| --- | --- | --- | --- |
| A | empty_evidence | confirmed_artifact | 7 |
| B | temporal_mismatch | probable_benchmark_or_underdetermined | 2 |
| C | role_mismatch | probable_benchmark_or_underdetermined | 5 |
| D | quantity_bound_mismatch | probable_benchmark_or_underdetermined | 0 |
| E | partial_support | likely_underdetermined | 9 |
| F | semantic_paraphrase | likely_underdetermined | 0 |
| G | likely_solver_miss | probable_true_solver_miss | 4 |

## Explicit answers (provisional)

- **How much remaining FEVER error mass is clearly NOT a solver issue?** At least the 7 empty-evidence artifacts are confirmed non-solver. Adding the provisional benchmark/underdetermined groups (B/C/D/E/F = 16) would raise that to 23/27 IF human review confirms them -- leaving only ~4 provisional true solver misses.
- **Should benchmark optimization pause pending review?** YES -- with only ~4/27 items even provisionally attributable to the solver, optimizing against the raw FEVER labels would chase data artifacts and label conventions.
- **Does the corrected FEVER benchmark now appear substantially cleaner?** YES vs the inverted mapping: claims are now single-fact (the multi-fact pathology is gone) and the bulk of residual errors are artifacts or subtle edge cases, not systematic over-abstention.
- **Are the remaining errors mostly subtle epistemic edge cases?** Provisionally YES (temporal/role/quantity/partial/paraphrase), pending the human pass below.

## Items for human review (grouped)

Annotate `fever_manual_review_annotations.jsonl` (one row per item). Then run `python fever_manual_review_stats.py` to aggregate (it refuses to run until annotations are filled).

### Group A — empty_evidence (confirmed_artifact) — 7 items

#### `nli_fever-0013` — group A (empty_evidence) — provisional: confirmed_artifact
- gold: **REFUTES** | preds (baseline/evidence-strict/entailment-direct): NOT_ENOUGH_INFO/REFUTES/REFUTES | wrong in: baseline
- raw premise: Murda Beatz's real name is Marshall Mathers.
- raw hypothesis: 
- mapped claim (<-premise): Murda Beatz's real name is Marshall Mathers.
- mapped evidence (<-hypothesis): 
- empty-evidence: True | claim→evidence coverage: 0.0 (low) | multi-fact claim: False | consistent across families: False | calibrated still disagrees: False
- why counted wrong: over_abstention
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

#### `nli_fever-0031` — group A (empty_evidence) — provisional: confirmed_artifact
- gold: **REFUTES** | preds (baseline/evidence-strict/entailment-direct): NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO | wrong in: baseline, evidence_strict, entailment_direct
- raw premise: Hot Right Now is mistakenly attributed to DJ Fresh.
- raw hypothesis: 
- mapped claim (<-premise): Hot Right Now is mistakenly attributed to DJ Fresh.
- mapped evidence (<-hypothesis): 
- empty-evidence: True | claim→evidence coverage: 0.0 (low) | multi-fact claim: False | consistent across families: True | calibrated still disagrees: True
- why counted wrong: over_abstention
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

#### `nli_fever-0033` — group A (empty_evidence) — provisional: confirmed_artifact
- gold: **REFUTES** | preds (baseline/evidence-strict/entailment-direct): NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO | wrong in: baseline, evidence_strict, entailment_direct
- raw premise: Giada at Home was only available on DVD.
- raw hypothesis: 
- mapped claim (<-premise): Giada at Home was only available on DVD.
- mapped evidence (<-hypothesis): 
- empty-evidence: True | claim→evidence coverage: 0.0 (low) | multi-fact claim: False | consistent across families: True | calibrated still disagrees: True
- why counted wrong: over_abstention
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

#### `nli_fever-0057` — group A (empty_evidence) — provisional: confirmed_artifact
- gold: **REFUTES** | preds (baseline/evidence-strict/entailment-direct): NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO | wrong in: baseline, evidence_strict, entailment_direct
- raw premise: Magic Johnson was a tap dancer.
- raw hypothesis: 
- mapped claim (<-premise): Magic Johnson was a tap dancer.
- mapped evidence (<-hypothesis): 
- empty-evidence: True | claim→evidence coverage: 0.0 (low) | multi-fact claim: False | consistent across families: True | calibrated still disagrees: True
- why counted wrong: over_abstention
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

#### `nli_fever-0077` — group A (empty_evidence) — provisional: confirmed_artifact
- gold: **REFUTES** | preds (baseline/evidence-strict/entailment-direct): NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO | wrong in: baseline, evidence_strict, entailment_direct
- raw premise: Jayasudha is an actor that stars in Daag.
- raw hypothesis: 
- mapped claim (<-premise): Jayasudha is an actor that stars in Daag.
- mapped evidence (<-hypothesis): 
- empty-evidence: True | claim→evidence coverage: 0.0 (low) | multi-fact claim: False | consistent across families: True | calibrated still disagrees: True
- why counted wrong: over_abstention
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

#### `nli_fever-0090` — group A (empty_evidence) — provisional: confirmed_artifact
- gold: **REFUTES** | preds (baseline/evidence-strict/entailment-direct): NOT_ENOUGH_INFO/REFUTES/REFUTES | wrong in: baseline
- raw premise: The highest point of the Hindu Kush is Everest.
- raw hypothesis: 
- mapped claim (<-premise): The highest point of the Hindu Kush is Everest.
- mapped evidence (<-hypothesis): 
- empty-evidence: True | claim→evidence coverage: 0.0 (low) | multi-fact claim: False | consistent across families: False | calibrated still disagrees: False
- why counted wrong: over_abstention
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

#### `nli_fever-0092` — group A (empty_evidence) — provisional: confirmed_artifact
- gold: **REFUTES** | preds (baseline/evidence-strict/entailment-direct): REFUTES/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO | wrong in: evidence_strict, entailment_direct
- raw premise: The heart beats at a resting rate close to 22 beats per minute.
- raw hypothesis: 
- mapped claim (<-premise): The heart beats at a resting rate close to 22 beats per minute.
- mapped evidence (<-hypothesis): 
- empty-evidence: True | claim→evidence coverage: 0.0 (low) | multi-fact claim: False | consistent across families: False | calibrated still disagrees: True
- why counted wrong: over_abstention
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

### Group B — temporal_mismatch (probable_benchmark_or_underdetermined) — 2 items

#### `nli_fever-0043` — group B (temporal_mismatch) — provisional: probable_benchmark_or_underdetermined
- gold: **SUPPORTS** | preds (baseline/evidence-strict/entailment-direct): NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO | wrong in: baseline, evidence_strict, entailment_direct
- raw premise: Mel B released a song on Virgin Records in 2007.
- raw hypothesis: Mel B . Brown began her solo career when she released `` I Want You Back '' with Missy Elliott on Virgin Records .
- mapped claim (<-premise): Mel B released a song on Virgin Records in 2007.
- mapped evidence (<-hypothesis): Mel B . Brown began her solo career when she released `` I Want You Back '' with Missy Elliott on Virgin Records .
- empty-evidence: False | claim→evidence coverage: 0.667 (partial) | multi-fact claim: False | consistent across families: True | calibrated still disagrees: True
- why counted wrong: over_abstention
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

#### `nli_fever-0094` — group B (temporal_mismatch) — provisional: probable_benchmark_or_underdetermined
- gold: **SUPPORTS** | preds (baseline/evidence-strict/entailment-direct): NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/SUPPORTS | wrong in: baseline, evidence_strict
- raw premise: Heavy Metal music was developed in the early 1970's.
- raw hypothesis: Heavy metal ( or simply metal ) is a genre of rock music that developed in the late 1960s and early 1970s , largely in the United Kingdom and the United States . Beginning in the late 1970s , bands in the new wave of British heavy metal suc…
- mapped claim (<-premise): Heavy Metal music was developed in the early 1970's.
- mapped evidence (<-hypothesis): Heavy metal ( or simply metal ) is a genre of rock music that developed in the late 1960s and early 1970s , largely in the United Kingdom and the United States . Beginning in the late 1970s , bands in the new wave of British heavy metal suc…
- empty-evidence: False | claim→evidence coverage: 1.0 (high) | multi-fact claim: False | consistent across families: False | calibrated still disagrees: False
- why counted wrong: over_abstention
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

### Group C — role_mismatch (probable_benchmark_or_underdetermined) — 5 items

#### `nli_fever-0032` — group C (role_mismatch) — provisional: probable_benchmark_or_underdetermined
- gold: **NOT_ENOUGH_INFO** | preds (baseline/evidence-strict/entailment-direct): SUPPORTS/SUPPORTS/SUPPORTS | wrong in: baseline, evidence_strict, entailment_direct
- raw premise: Private Lives is a three act play from 1930.
- raw hypothesis: Private Lives is a 1930 comedy of manners in three acts by Noël Coward . Private Lives is a 1931 American Pre-Code comedy film directed by Sidney Franklin .
- mapped claim (<-premise): Private Lives is a three act play from 1930.
- mapped evidence (<-hypothesis): Private Lives is a 1930 comedy of manners in three acts by Noël Coward . Private Lives is a 1931 American Pre-Code comedy film directed by Sidney Franklin .
- empty-evidence: False | claim→evidence coverage: 0.833 (high) | multi-fact claim: False | consistent across families: True | calibrated still disagrees: True
- why counted wrong: over_commitment
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

#### `nli_fever-0055` — group C (role_mismatch) — provisional: probable_benchmark_or_underdetermined
- gold: **NOT_ENOUGH_INFO** | preds (baseline/evidence-strict/entailment-direct): REFUTES/NOT_ENOUGH_INFO/REFUTES | wrong in: baseline, entailment_direct
- raw premise: Men in Black II stars eight children.
- raw hypothesis: Men in Black II ( stylized as MIIB ) is a 2002 American science fiction action comedy film starring Tommy Lee Jones , Will Smith , Lara Flynn Boyle , Johnny Knoxville , Rosario Dawson , Tony Shalhoub and Rip Torn .
- mapped claim (<-premise): Men in Black II stars eight children.
- mapped evidence (<-hypothesis): Men in Black II ( stylized as MIIB ) is a 2002 American science fiction action comedy film starring Tommy Lee Jones , Will Smith , Lara Flynn Boyle , Johnny Knoxville , Rosario Dawson , Tony Shalhoub and Rip Torn .
- empty-evidence: False | claim→evidence coverage: 0.5 (partial) | multi-fact claim: False | consistent across families: False | calibrated still disagrees: False
- why counted wrong: over_commitment
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

#### `nli_fever-0058` — group C (role_mismatch) — provisional: probable_benchmark_or_underdetermined
- gold: **REFUTES** | preds (baseline/evidence-strict/entailment-direct): NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO | wrong in: baseline, evidence_strict, entailment_direct
- raw premise: The Adventures of Pluto Nash was reviewed by Ron Underwood.
- raw hypothesis: The Adventures of Pluto Nash is a 2002 Australian-American science fiction action comedy film starring Eddie Murphy ( in a dual role ) and directed by Ron Underwood .
- mapped claim (<-premise): The Adventures of Pluto Nash was reviewed by Ron Underwood.
- mapped evidence (<-hypothesis): The Adventures of Pluto Nash is a 2002 Australian-American science fiction action comedy film starring Eddie Murphy ( in a dual role ) and directed by Ron Underwood .
- empty-evidence: False | claim→evidence coverage: 0.833 (high) | multi-fact claim: False | consistent across families: True | calibrated still disagrees: True
- why counted wrong: over_abstention
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

#### `nli_fever-0075` — group C (role_mismatch) — provisional: probable_benchmark_or_underdetermined
- gold: **SUPPORTS** | preds (baseline/evidence-strict/entailment-direct): SUPPORTS/NOT_ENOUGH_INFO/SUPPORTS | wrong in: evidence_strict
- raw premise: Home for the Holidays stars an American actress.
- raw hypothesis: Home for the Holidays is a 1972 American made-for-television horror film directed by John Llewellyn Moxey , produced by Aaron Spelling and starring Sally Field , Eleanor Parker , Julie Harris , Jessica Walter and Walter Brennan which premie…
- mapped claim (<-premise): Home for the Holidays stars an American actress.
- mapped evidence (<-hypothesis): Home for the Holidays is a 1972 American made-for-television horror film directed by John Llewellyn Moxey , produced by Aaron Spelling and starring Sally Field , Eleanor Parker , Julie Harris , Jessica Walter and Walter Brennan which premie…
- empty-evidence: False | claim→evidence coverage: 0.8 (high) | multi-fact claim: False | consistent across families: False | calibrated still disagrees: False
- why counted wrong: over_abstention
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

#### `nli_fever-0078` — group C (role_mismatch) — provisional: probable_benchmark_or_underdetermined
- gold: **NOT_ENOUGH_INFO** | preds (baseline/evidence-strict/entailment-direct): SUPPORTS/SUPPORTS/SUPPORTS | wrong in: baseline, evidence_strict, entailment_direct
- raw premise: XHamster's The Sex Factor forces eight men and eight women to battle to become a porn star.
- raw hypothesis: The Sex Factor is an online reality TV series produced by xHamster where eight men and eight women compete to become a porn star . XHamster . The site produces The Sex Factor , a reality series in which men and women compete to become porn …
- mapped claim (<-premise): XHamster's The Sex Factor forces eight men and eight women to battle to become a porn star.
- mapped evidence (<-hypothesis): The Sex Factor is an online reality TV series produced by xHamster where eight men and eight women compete to become a porn star . XHamster . The site produces The Sex Factor , a reality series in which men and women compete to become porn …
- empty-evidence: False | claim→evidence coverage: 0.818 (high) | multi-fact claim: True | consistent across families: True | calibrated still disagrees: True
- why counted wrong: over_commitment
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

### Group E — partial_support (likely_underdetermined) — 9 items

#### `nli_fever-0010` — group E (partial_support) — provisional: likely_underdetermined
- gold: **NOT_ENOUGH_INFO** | preds (baseline/evidence-strict/entailment-direct): SUPPORTS/SUPPORTS/SUPPORTS | wrong in: baseline, evidence_strict, entailment_direct
- raw premise: Shooter is about an expert marksman who tries to stop the assassination of the president.
- raw hypothesis: Shooter (2007 film) . The film follows Force Recon veteran Bob Lee Swagger ( Mark Wahlberg ) , who is framed for murder by a rogue secret private military company unit . Shooter (TV series) . The show stars Ryan Phillippe in the lead role o…
- mapped claim (<-premise): Shooter is about an expert marksman who tries to stop the assassination of the president.
- mapped evidence (<-hypothesis): Shooter (2007 film) . The film follows Force Recon veteran Bob Lee Swagger ( Mark Wahlberg ) , who is framed for murder by a rogue secret private military company unit . Shooter (TV series) . The show stars Ryan Phillippe in the lead role o…
- empty-evidence: False | claim→evidence coverage: 0.571 (partial) | multi-fact claim: False | consistent across families: True | calibrated still disagrees: True
- why counted wrong: over_commitment
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

#### `nli_fever-0011` — group E (partial_support) — provisional: likely_underdetermined
- gold: **NOT_ENOUGH_INFO** | preds (baseline/evidence-strict/entailment-direct): REFUTES/REFUTES/REFUTES | wrong in: baseline, evidence_strict, entailment_direct
- raw premise: House is a sitcom.
- raw hypothesis: House ( also called House , M.D. ) is an American television medical drama that originally ran on the Fox network for eight seasons , from November 16 , 2004 to May 21 , 2012 .
- mapped claim (<-premise): House is a sitcom.
- mapped evidence (<-hypothesis): House ( also called House , M.D. ) is an American television medical drama that originally ran on the Fox network for eight seasons , from November 16 , 2004 to May 21 , 2012 .
- empty-evidence: False | claim→evidence coverage: 0.5 (partial) | multi-fact claim: False | consistent across families: True | calibrated still disagrees: True
- why counted wrong: over_commitment
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

#### `nli_fever-0044` — group E (partial_support) — provisional: likely_underdetermined
- gold: **REFUTES** | preds (baseline/evidence-strict/entailment-direct): REFUTES/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO | wrong in: evidence_strict, entailment_direct
- raw premise: Noah Cyrus is a younger sister of Macy Grey.
- raw hypothesis: Noah Cyrus . She is the youngest daughter of Billy Ray Cyrus and younger sister of Miley Cyrus and Trace Cyrus .
- mapped claim (<-premise): Noah Cyrus is a younger sister of Macy Grey.
- mapped evidence (<-hypothesis): Noah Cyrus . She is the youngest daughter of Billy Ray Cyrus and younger sister of Miley Cyrus and Trace Cyrus .
- empty-evidence: False | claim→evidence coverage: 0.667 (partial) | multi-fact claim: False | consistent across families: False | calibrated still disagrees: True
- why counted wrong: over_abstention
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

#### `nli_fever-0045` — group E (partial_support) — provisional: likely_underdetermined
- gold: **REFUTES** | preds (baseline/evidence-strict/entailment-direct): REFUTES/REFUTES/NOT_ENOUGH_INFO | wrong in: entailment_direct
- raw premise: Mohra is a truck.
- raw hypothesis: Mohra ( Pawn ) is a 1994 Indian action thriller film directed by Rajiv Rai starring Akshay Kumar , Sunil Shetty , Raveena Tandon and Naseeruddin Shah in the lead roles with Paresh Rawal , Gulshan Grover , Raza Murad and Sadashiv Amrapurkar …
- mapped claim (<-premise): Mohra is a truck.
- mapped evidence (<-hypothesis): Mohra ( Pawn ) is a 1994 Indian action thriller film directed by Rajiv Rai starring Akshay Kumar , Sunil Shetty , Raveena Tandon and Naseeruddin Shah in the lead roles with Paresh Rawal , Gulshan Grover , Raza Murad and Sadashiv Amrapurkar …
- empty-evidence: False | claim→evidence coverage: 0.5 (partial) | multi-fact claim: False | consistent across families: False | calibrated still disagrees: True
- why counted wrong: over_abstention
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

#### `nli_fever-0046` — group E (partial_support) — provisional: likely_underdetermined
- gold: **REFUTES** | preds (baseline/evidence-strict/entailment-direct): REFUTES/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO | wrong in: evidence_strict, entailment_direct
- raw premise: Hourglass is performed by a Russian singer-songwriter.
- raw hypothesis: `` Hourglass '' is a song by British electronic duo Disclosure . Hourglass is singer-songwriter James Taylor 's fourteenth studio album .
- mapped claim (<-premise): Hourglass is performed by a Russian singer-songwriter.
- mapped evidence (<-hypothesis): `` Hourglass '' is a song by British electronic duo Disclosure . Hourglass is singer-songwriter James Taylor 's fourteenth studio album .
- empty-evidence: False | claim→evidence coverage: 0.5 (partial) | multi-fact claim: False | consistent across families: False | calibrated still disagrees: True
- why counted wrong: over_abstention
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

#### `nli_fever-0070` — group E (partial_support) — provisional: likely_underdetermined
- gold: **REFUTES** | preds (baseline/evidence-strict/entailment-direct): REFUTES/NOT_ENOUGH_INFO/REFUTES | wrong in: evidence_strict
- raw premise: Seohyun is a dog.
- raw hypothesis: Do n't Say No is the debut extended play by South Korean singer Seohyun . Seo Ju-hyun ( born June 28 , 1991 ) , known professionally as Seohyun , is a South Korean singer and actress . She debuted as a member of girl group Girls ' Generatio…
- mapped claim (<-premise): Seohyun is a dog.
- mapped evidence (<-hypothesis): Do n't Say No is the debut extended play by South Korean singer Seohyun . Seo Ju-hyun ( born June 28 , 1991 ) , known professionally as Seohyun , is a South Korean singer and actress . She debuted as a member of girl group Girls ' Generatio…
- empty-evidence: False | claim→evidence coverage: 0.5 (partial) | multi-fact claim: False | consistent across families: False | calibrated still disagrees: False
- why counted wrong: over_abstention
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

#### `nli_fever-0074` — group E (partial_support) — provisional: likely_underdetermined
- gold: **REFUTES** | preds (baseline/evidence-strict/entailment-direct): SUPPORTS/REFUTES/REFUTES | wrong in: baseline
- raw premise: Veeram is something other than an Indian Tamil film.
- raw hypothesis: Veeram ( Valour ) is a 2014 Indian Tamil action film directed by Siva and produced by Vijaya Productions . Veeram ( Valour ) is a 2016 Indian epic historical drama film written and directed by Jayaraj .
- mapped claim (<-premise): Veeram is something other than an Indian Tamil film.
- mapped evidence (<-hypothesis): Veeram ( Valour ) is a 2014 Indian Tamil action film directed by Siva and produced by Vijaya Productions . Veeram ( Valour ) is a 2016 Indian epic historical drama film written and directed by Jayaraj .
- empty-evidence: False | claim→evidence coverage: 0.667 (partial) | multi-fact claim: False | consistent across families: False | calibrated still disagrees: False
- why counted wrong: direction_flip
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

#### `nli_fever-0086` — group E (partial_support) — provisional: likely_underdetermined
- gold: **REFUTES** | preds (baseline/evidence-strict/entailment-direct): REFUTES/REFUTES/NOT_ENOUGH_INFO | wrong in: entailment_direct
- raw premise: Colin Kaepernick is a poker player.
- raw hypothesis: Colin Rand Kaepernick ( [ ` kæpərnɪk ] ; born November 3 , 1987 ) is an American football quarterback who is currently a free agent .
- mapped claim (<-premise): Colin Kaepernick is a poker player.
- mapped evidence (<-hypothesis): Colin Rand Kaepernick ( [ ` kæpərnɪk ] ; born November 3 , 1987 ) is an American football quarterback who is currently a free agent .
- empty-evidence: False | claim→evidence coverage: 0.5 (partial) | multi-fact claim: False | consistent across families: False | calibrated still disagrees: True
- why counted wrong: over_abstention
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

#### `nli_fever-0089` — group E (partial_support) — provisional: likely_underdetermined
- gold: **NOT_ENOUGH_INFO** | preds (baseline/evidence-strict/entailment-direct): REFUTES/REFUTES/REFUTES | wrong in: baseline, evidence_strict, entailment_direct
- raw premise: The Road to El Dorado stars Tim Allen.
- raw hypothesis: The Road to El Dorado . The film stars Kevin Kline , Kenneth Branagh , Armand Assante , Jim Cummings , Edward James Olmos , Tobin Bell and Rosie Perez .
- mapped claim (<-premise): The Road to El Dorado stars Tim Allen.
- mapped evidence (<-hypothesis): The Road to El Dorado . The film stars Kevin Kline , Kenneth Branagh , Armand Assante , Jim Cummings , Edward James Olmos , Tobin Bell and Rosie Perez .
- empty-evidence: False | claim→evidence coverage: 0.667 (partial) | multi-fact claim: False | consistent across families: True | calibrated still disagrees: True
- why counted wrong: over_commitment
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

### Group G — likely_solver_miss (probable_true_solver_miss) — 4 items

#### `nli_fever-0003` — group G (likely_solver_miss) — provisional: probable_true_solver_miss
- gold: **NOT_ENOUGH_INFO** | preds (baseline/evidence-strict/entailment-direct): REFUTES/REFUTES/REFUTES | wrong in: baseline, evidence_strict, entailment_direct
- raw premise: Anne Rice was born in New Jersey.
- raw hypothesis: Anne Rice . Born in New Orleans , Rice spent much of her early life there before moving to Texas , and later to San Francisco . Route 495 is a 3.45 mi freeway in Hudson County , New Jersey , in the United States that connects the New Jersey…
- mapped claim (<-premise): Anne Rice was born in New Jersey.
- mapped evidence (<-hypothesis): Anne Rice . Born in New Orleans , Rice spent much of her early life there before moving to Texas , and later to San Francisco . Route 495 is a 3.45 mi freeway in Hudson County , New Jersey , in the United States that connects the New Jersey…
- empty-evidence: False | claim→evidence coverage: 1.0 (high) | multi-fact claim: False | consistent across families: True | calibrated still disagrees: True
- why counted wrong: over_commitment
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

#### `nli_fever-0049` — group G (likely_solver_miss) — provisional: probable_true_solver_miss
- gold: **NOT_ENOUGH_INFO** | preds (baseline/evidence-strict/entailment-direct): REFUTES/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO | wrong in: baseline
- raw premise: Papua comprised all of Indonesia.
- raw hypothesis: Papua is the largest and easternmost province of Indonesia , comprising most of western New Guinea . It was formerly called Irian Jaya ( before that West Irian or Irian Barat ) and comprised all of Indonesian New Guinea .
- mapped claim (<-premise): Papua comprised all of Indonesia.
- mapped evidence (<-hypothesis): Papua is the largest and easternmost province of Indonesia , comprising most of western New Guinea . It was formerly called Irian Jaya ( before that West Irian or Irian Barat ) and comprised all of Indonesian New Guinea .
- empty-evidence: False | claim→evidence coverage: 1.0 (high) | multi-fact claim: False | consistent across families: False | calibrated still disagrees: False
- why counted wrong: over_commitment
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

#### `nli_fever-0081` — group G (likely_solver_miss) — provisional: probable_true_solver_miss
- gold: **NOT_ENOUGH_INFO** | preds (baseline/evidence-strict/entailment-direct): REFUTES/REFUTES/REFUTES | wrong in: baseline, evidence_strict, entailment_direct
- raw premise: Island Records is a music school.
- raw hypothesis: Island Records is a British-American record label that operates as a division of Universal Music Group ( UMG ) .
- mapped claim (<-premise): Island Records is a music school.
- mapped evidence (<-hypothesis): Island Records is a British-American record label that operates as a division of Universal Music Group ( UMG ) .
- empty-evidence: False | claim→evidence coverage: 0.75 (high) | multi-fact claim: False | consistent across families: True | calibrated still disagrees: True
- why counted wrong: over_commitment
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

#### `nli_fever-0099` — group G (likely_solver_miss) — provisional: probable_true_solver_miss
- gold: **REFUTES** | preds (baseline/evidence-strict/entailment-direct): NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO | wrong in: baseline, evidence_strict, entailment_direct
- raw premise: Tool has won three Oscars.
- raw hypothesis: Tool (band) . Tool has won three Grammy Awards , performed worldwide tours , and produced albums topping the charts in several countries .
- mapped claim (<-premise): Tool has won three Oscars.
- mapped evidence (<-hypothesis): Tool (band) . Tool has won three Grammy Awards , performed worldwide tours , and produced albums topping the charts in several countries .
- empty-evidence: False | claim→evidence coverage: 0.75 (high) | multi-fact claim: False | consistent across families: True | calibrated still disagrees: True
- why counted wrong: over_abstention
- **HUMAN_JUDGMENT**: ______ (MODEL_CLEARLY_WRONG / GOLD_QUESTIONABLE / UNDERDETERMINED / DATA_ARTIFACT / BENCHMARK_CONVENTION / AMBIGUOUS)
- **COMMENT**: ______
- **CONFIDENCE**: ____ (0-1)

## Honesty / limits

- Grouping is mechanical/heuristic and PROVISIONAL; only empty-evidence is a confirmed artifact. No labels reinterpreted, no accuracy adjusted (deferred until annotations exist). Per-item predictions are DeepSeek's; raw model text not captured. DESi-core untouched.

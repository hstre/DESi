# Corrected-FEVER remaining-error audit

Mechanical dump of every case where DeepSeek's parsed verdict disagrees with the gold label on NLI-FEVER under the **corrected** mapping (claim<-premise, evidence<-hypothesis). Source: corrected `re_nli_fever.json` (DeepSeek v4 Pro, the only run with per-item predictions across all three prompt families). No model calls, no reruns, no fixes. `model_raw_output` is not captured (runners stored the parsed verdict only).

Distinct wrong items: **27** of 100. Wrong (item, prompt-family) cases: **60**.

## Error-type distribution (mechanical)

| why wrong | (item,family) cases |
| --- | --- |
| over_abstention | 35 |
| over_commitment | 24 |
| direction_flip | 1 |

Dominant class (mechanical): **over_abstention** (35 cases). By prompt family: baseline 20, evidence_strict 20, entailment_direct 20.

> **Data-artifact sub-class:** 7 of 27 wrong items have an **EMPTY evidence field** (raw `hypothesis` blank). On those the model correctly returns NEI but gold is SUPPORTS/REFUTES, so they are counted as over_abstention but are dataset artifacts, NOT model errors. Subtract them to estimate genuine over-abstention.

Mechanical aggregate signals over wrong items: multi-fact claim = 1/27; empty evidence = 7; claim→evidence overlap band low/partial/high = 7/11/9; consistent across all families = 14; calibrated-prompt still disagrees = 19.

## Wrong items (grouped; corrected mapping applied)

Per item: gold, the three family predictions (baseline/evidence-strict/entailment-direct), and mechanical flags. Human fields (`evidence_explicitly_supports_refutes`, `label_underdetermined_or_questionable`) are blank in the JSONL for annotation.

#### `nli_fever-0031` — gold REFUTES | preds (b/e/ent): NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO
- wrong in: baseline, evidence_strict, entailment_direct
- mapped claim (<-premise): Hot Right Now is mistakenly attributed to DJ Fresh.
- mapped evidence (<-hypothesis): 
- multi-fact claim: False | claim→evidence coverage: 0.0 (low) | consistent across families: True | calibrated still disagrees: True
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0033` — gold REFUTES | preds (b/e/ent): NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO
- wrong in: baseline, evidence_strict, entailment_direct
- mapped claim (<-premise): Giada at Home was only available on DVD.
- mapped evidence (<-hypothesis): 
- multi-fact claim: False | claim→evidence coverage: 0.0 (low) | consistent across families: True | calibrated still disagrees: True
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0043` — gold SUPPORTS | preds (b/e/ent): NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO
- wrong in: baseline, evidence_strict, entailment_direct
- mapped claim (<-premise): Mel B released a song on Virgin Records in 2007.
- mapped evidence (<-hypothesis): Mel B . Brown began her solo career when she released `` I Want You Back '' with Missy Elliott on Virgin Records .
- multi-fact claim: False | claim→evidence coverage: 0.667 (partial) | consistent across families: True | calibrated still disagrees: True
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0057` — gold REFUTES | preds (b/e/ent): NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO
- wrong in: baseline, evidence_strict, entailment_direct
- mapped claim (<-premise): Magic Johnson was a tap dancer.
- mapped evidence (<-hypothesis): 
- multi-fact claim: False | claim→evidence coverage: 0.0 (low) | consistent across families: True | calibrated still disagrees: True
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0058` — gold REFUTES | preds (b/e/ent): NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO
- wrong in: baseline, evidence_strict, entailment_direct
- mapped claim (<-premise): The Adventures of Pluto Nash was reviewed by Ron Underwood.
- mapped evidence (<-hypothesis): The Adventures of Pluto Nash is a 2002 Australian-American science fiction action comedy film starring Eddie Murphy ( in a dual role ) and directed by Ron Underwood .
- multi-fact claim: False | claim→evidence coverage: 0.833 (high) | consistent across families: True | calibrated still disagrees: True
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0077` — gold REFUTES | preds (b/e/ent): NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO
- wrong in: baseline, evidence_strict, entailment_direct
- mapped claim (<-premise): Jayasudha is an actor that stars in Daag.
- mapped evidence (<-hypothesis): 
- multi-fact claim: False | claim→evidence coverage: 0.0 (low) | consistent across families: True | calibrated still disagrees: True
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0099` — gold REFUTES | preds (b/e/ent): NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO
- wrong in: baseline, evidence_strict, entailment_direct
- mapped claim (<-premise): Tool has won three Oscars.
- mapped evidence (<-hypothesis): Tool (band) . Tool has won three Grammy Awards , performed worldwide tours , and produced albums topping the charts in several countries .
- multi-fact claim: False | claim→evidence coverage: 0.75 (high) | consistent across families: True | calibrated still disagrees: True
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0013` — gold REFUTES | preds (b/e/ent): NOT_ENOUGH_INFO/REFUTES/REFUTES
- wrong in: baseline
- mapped claim (<-premise): Murda Beatz's real name is Marshall Mathers.
- mapped evidence (<-hypothesis): 
- multi-fact claim: False | claim→evidence coverage: 0.0 (low) | consistent across families: False | calibrated still disagrees: False
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0044` — gold REFUTES | preds (b/e/ent): REFUTES/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO
- wrong in: evidence_strict, entailment_direct
- mapped claim (<-premise): Noah Cyrus is a younger sister of Macy Grey.
- mapped evidence (<-hypothesis): Noah Cyrus . She is the youngest daughter of Billy Ray Cyrus and younger sister of Miley Cyrus and Trace Cyrus .
- multi-fact claim: False | claim→evidence coverage: 0.667 (partial) | consistent across families: False | calibrated still disagrees: True
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0045` — gold REFUTES | preds (b/e/ent): REFUTES/REFUTES/NOT_ENOUGH_INFO
- wrong in: entailment_direct
- mapped claim (<-premise): Mohra is a truck.
- mapped evidence (<-hypothesis): Mohra ( Pawn ) is a 1994 Indian action thriller film directed by Rajiv Rai starring Akshay Kumar , Sunil Shetty , Raveena Tandon and Naseeruddin Shah in the lead roles with Paresh Rawal , Gulshan Grov…
- multi-fact claim: False | claim→evidence coverage: 0.5 (partial) | consistent across families: False | calibrated still disagrees: True
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0046` — gold REFUTES | preds (b/e/ent): REFUTES/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO
- wrong in: evidence_strict, entailment_direct
- mapped claim (<-premise): Hourglass is performed by a Russian singer-songwriter.
- mapped evidence (<-hypothesis): `` Hourglass '' is a song by British electronic duo Disclosure . Hourglass is singer-songwriter James Taylor 's fourteenth studio album .
- multi-fact claim: False | claim→evidence coverage: 0.5 (partial) | consistent across families: False | calibrated still disagrees: True
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0070` — gold REFUTES | preds (b/e/ent): REFUTES/NOT_ENOUGH_INFO/REFUTES
- wrong in: evidence_strict
- mapped claim (<-premise): Seohyun is a dog.
- mapped evidence (<-hypothesis): Do n't Say No is the debut extended play by South Korean singer Seohyun . Seo Ju-hyun ( born June 28 , 1991 ) , known professionally as Seohyun , is a South Korean singer and actress . She debuted as …
- multi-fact claim: False | claim→evidence coverage: 0.5 (partial) | consistent across families: False | calibrated still disagrees: False
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0075` — gold SUPPORTS | preds (b/e/ent): SUPPORTS/NOT_ENOUGH_INFO/SUPPORTS
- wrong in: evidence_strict
- mapped claim (<-premise): Home for the Holidays stars an American actress.
- mapped evidence (<-hypothesis): Home for the Holidays is a 1972 American made-for-television horror film directed by John Llewellyn Moxey , produced by Aaron Spelling and starring Sally Field , Eleanor Parker , Julie Harris , Jessic…
- multi-fact claim: False | claim→evidence coverage: 0.8 (high) | consistent across families: False | calibrated still disagrees: False
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0086` — gold REFUTES | preds (b/e/ent): REFUTES/REFUTES/NOT_ENOUGH_INFO
- wrong in: entailment_direct
- mapped claim (<-premise): Colin Kaepernick is a poker player.
- mapped evidence (<-hypothesis): Colin Rand Kaepernick ( [ ` kæpərnɪk ] ; born November 3 , 1987 ) is an American football quarterback who is currently a free agent .
- multi-fact claim: False | claim→evidence coverage: 0.5 (partial) | consistent across families: False | calibrated still disagrees: True
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0090` — gold REFUTES | preds (b/e/ent): NOT_ENOUGH_INFO/REFUTES/REFUTES
- wrong in: baseline
- mapped claim (<-premise): The highest point of the Hindu Kush is Everest.
- mapped evidence (<-hypothesis): 
- multi-fact claim: False | claim→evidence coverage: 0.0 (low) | consistent across families: False | calibrated still disagrees: False
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0092` — gold REFUTES | preds (b/e/ent): REFUTES/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO
- wrong in: evidence_strict, entailment_direct
- mapped claim (<-premise): The heart beats at a resting rate close to 22 beats per minute.
- mapped evidence (<-hypothesis): 
- multi-fact claim: False | claim→evidence coverage: 0.0 (low) | consistent across families: False | calibrated still disagrees: True
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0094` — gold SUPPORTS | preds (b/e/ent): NOT_ENOUGH_INFO/NOT_ENOUGH_INFO/SUPPORTS
- wrong in: baseline, evidence_strict
- mapped claim (<-premise): Heavy Metal music was developed in the early 1970's.
- mapped evidence (<-hypothesis): Heavy metal ( or simply metal ) is a genre of rock music that developed in the late 1960s and early 1970s , largely in the United Kingdom and the United States . Beginning in the late 1970s , bands in…
- multi-fact claim: False | claim→evidence coverage: 1.0 (high) | consistent across families: False | calibrated still disagrees: False
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0074` — gold REFUTES | preds (b/e/ent): SUPPORTS/REFUTES/REFUTES
- wrong in: baseline
- mapped claim (<-premise): Veeram is something other than an Indian Tamil film.
- mapped evidence (<-hypothesis): Veeram ( Valour ) is a 2014 Indian Tamil action film directed by Siva and produced by Vijaya Productions . Veeram ( Valour ) is a 2016 Indian epic historical drama film written and directed by Jayaraj…
- multi-fact claim: False | claim→evidence coverage: 0.667 (partial) | consistent across families: False | calibrated still disagrees: False
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0003` — gold NOT_ENOUGH_INFO | preds (b/e/ent): REFUTES/REFUTES/REFUTES
- wrong in: baseline, evidence_strict, entailment_direct
- mapped claim (<-premise): Anne Rice was born in New Jersey.
- mapped evidence (<-hypothesis): Anne Rice . Born in New Orleans , Rice spent much of her early life there before moving to Texas , and later to San Francisco . Route 495 is a 3.45 mi freeway in Hudson County , New Jersey , in the Un…
- multi-fact claim: False | claim→evidence coverage: 1.0 (high) | consistent across families: True | calibrated still disagrees: True
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0010` — gold NOT_ENOUGH_INFO | preds (b/e/ent): SUPPORTS/SUPPORTS/SUPPORTS
- wrong in: baseline, evidence_strict, entailment_direct
- mapped claim (<-premise): Shooter is about an expert marksman who tries to stop the assassination of the president.
- mapped evidence (<-hypothesis): Shooter (2007 film) . The film follows Force Recon veteran Bob Lee Swagger ( Mark Wahlberg ) , who is framed for murder by a rogue secret private military company unit . Shooter (TV series) . The show…
- multi-fact claim: False | claim→evidence coverage: 0.571 (partial) | consistent across families: True | calibrated still disagrees: True
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0011` — gold NOT_ENOUGH_INFO | preds (b/e/ent): REFUTES/REFUTES/REFUTES
- wrong in: baseline, evidence_strict, entailment_direct
- mapped claim (<-premise): House is a sitcom.
- mapped evidence (<-hypothesis): House ( also called House , M.D. ) is an American television medical drama that originally ran on the Fox network for eight seasons , from November 16 , 2004 to May 21 , 2012 .
- multi-fact claim: False | claim→evidence coverage: 0.5 (partial) | consistent across families: True | calibrated still disagrees: True
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0032` — gold NOT_ENOUGH_INFO | preds (b/e/ent): SUPPORTS/SUPPORTS/SUPPORTS
- wrong in: baseline, evidence_strict, entailment_direct
- mapped claim (<-premise): Private Lives is a three act play from 1930.
- mapped evidence (<-hypothesis): Private Lives is a 1930 comedy of manners in three acts by Noël Coward . Private Lives is a 1931 American Pre-Code comedy film directed by Sidney Franklin .
- multi-fact claim: False | claim→evidence coverage: 0.833 (high) | consistent across families: True | calibrated still disagrees: True
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0078` — gold NOT_ENOUGH_INFO | preds (b/e/ent): SUPPORTS/SUPPORTS/SUPPORTS
- wrong in: baseline, evidence_strict, entailment_direct
- mapped claim (<-premise): XHamster's The Sex Factor forces eight men and eight women to battle to become a porn star.
- mapped evidence (<-hypothesis): The Sex Factor is an online reality TV series produced by xHamster where eight men and eight women compete to become a porn star . XHamster . The site produces The Sex Factor , a reality series in whi…
- multi-fact claim: True | claim→evidence coverage: 0.818 (high) | consistent across families: True | calibrated still disagrees: True
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0081` — gold NOT_ENOUGH_INFO | preds (b/e/ent): REFUTES/REFUTES/REFUTES
- wrong in: baseline, evidence_strict, entailment_direct
- mapped claim (<-premise): Island Records is a music school.
- mapped evidence (<-hypothesis): Island Records is a British-American record label that operates as a division of Universal Music Group ( UMG ) .
- multi-fact claim: False | claim→evidence coverage: 0.75 (high) | consistent across families: True | calibrated still disagrees: True
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0089` — gold NOT_ENOUGH_INFO | preds (b/e/ent): REFUTES/REFUTES/REFUTES
- wrong in: baseline, evidence_strict, entailment_direct
- mapped claim (<-premise): The Road to El Dorado stars Tim Allen.
- mapped evidence (<-hypothesis): The Road to El Dorado . The film stars Kevin Kline , Kenneth Branagh , Armand Assante , Jim Cummings , Edward James Olmos , Tobin Bell and Rosie Perez .
- multi-fact claim: False | claim→evidence coverage: 0.667 (partial) | consistent across families: True | calibrated still disagrees: True
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0049` — gold NOT_ENOUGH_INFO | preds (b/e/ent): REFUTES/NOT_ENOUGH_INFO/NOT_ENOUGH_INFO
- wrong in: baseline
- mapped claim (<-premise): Papua comprised all of Indonesia.
- mapped evidence (<-hypothesis): Papua is the largest and easternmost province of Indonesia , comprising most of western New Guinea . It was formerly called Irian Jaya ( before that West Irian or Irian Barat ) and comprised all of In…
- multi-fact claim: False | claim→evidence coverage: 1.0 (high) | consistent across families: False | calibrated still disagrees: False
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

#### `nli_fever-0055` — gold NOT_ENOUGH_INFO | preds (b/e/ent): REFUTES/NOT_ENOUGH_INFO/REFUTES
- wrong in: baseline, entailment_direct
- mapped claim (<-premise): Men in Black II stars eight children.
- mapped evidence (<-hypothesis): Men in Black II ( stylized as MIIB ) is a 2002 American science fiction action comedy film starring Tommy Lee Jones , Will Smith , Lara Flynn Boyle , Johnny Knoxville , Rosario Dawson , Tony Shalhoub …
- multi-fact claim: False | claim→evidence coverage: 0.5 (partial) | consistent across families: False | calibrated still disagrees: False
- evidence_explicitly_supports_refutes: ______ | label_underdetermined_or_questionable: ______

## How to read / next step

- `claim→evidence coverage` is a MECHANICAL lexical proxy for whether the evidence contains the claim's content (not a judgment of support/refute). `multi-fact claim` is a heuristic. The actual support/refute and label-quality calls are left to human annotation in `fever_corrected_error_cases.jsonl`.
- Decide which class dominates from the error-type distribution above before any further action.

## Honesty / limits

- Corrected mapping only; per-item dump is DeepSeek (the only model with stored per-item predictions; Claude/GPT/Granite corrected runs stored aggregates only). Raw model output not captured. No model calls, no reruns, no relabeling. Public dataset text. DESi-core untouched.

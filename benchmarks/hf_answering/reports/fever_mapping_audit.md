# FEVER premise/hypothesis mapping audit

**Was the FEVER mapping inverted? YES.** `pietrolesci/nli_fever` stores its columns opposite to standard NLI naming: the **`premise`** field contains the short FEVER **claim** to verify, and the **`hypothesis`** field contains the long Wikipedia **evidence**. The verify task is "does EVIDENCE support CLAIM", scored against `fever_gold_label`.

- Old (buggy) mapping: `claim<-hypothesis, evidence<-premise (INVERTED)` -> fed a *long multi-fact claim* against a *short evidence*, mechanically forcing NOT_ENOUGH_INFO (the chronic FEVER over-abstention).
- Corrected mapping: `claim<-premise, evidence<-hypothesis (CORRECTED)`. Labels unchanged (normalize_gold reads only `fever_gold_label`).

## Orientation stats over the first 300 dev items (mechanical)

| mapping | median claim len | median evidence len | claim > 2x evidence | evidence > 2x claim | empty claim | empty evidence |
| --- | --- | --- | --- | --- | --- | --- |
| OLD (inverted) | 221 | 46 | 252 | 0 | 27 | 0 |
| CORRECTED | 46 | 221 | 0 | 252 | 0 | 27 |

Under the OLD mapping the claim dwarfs the evidence on most items (inverted); under the CORRECTED mapping the evidence is the longer field, as a verify task expects.

## Raw examples (corrected mapping applied)

#### dev[0] — gold = NOT ENOUGH INFO
- raw **premise** (108 chars): Colin Kaepernick became a starting quarterback during the 49ers 63rd season in the National Football League.
- raw **hypothesis** (372 chars): Colin Kaepernick . Kaepernick began his professional career as a backup to Alex Smith , but became the 49ers ' starter in the middle of the 2012 season after Sm…
- => mapped **claim** (from premise): Colin Kaepernick became a starting quarterback during the 49ers 63rd season in the National Football League.
- => mapped **evidence** (from hypothesis): Colin Kaepernick . Kaepernick began his professional career as a backup to Alex Smith , but became the 49ers ' starter in the middle of the 2012 season after Sm…

#### dev[1] — gold = NOT ENOUGH INFO
- raw **premise** (25 chars): Tilda Swinton is a vegan.
- raw **hypothesis** (190 chars): Katherine Matilda `` Tilda '' Swinton ( born 5 November 1960 ) is a British actress , performance artist , model , and fashion muse , known for her roles in ind…
- => mapped **claim** (from premise): Tilda Swinton is a vegan.
- => mapped **evidence** (from hypothesis): Katherine Matilda `` Tilda '' Swinton ( born 5 November 1960 ) is a British actress , performance artist , model , and fashion muse , known for her roles in ind…

#### dev[2] — gold = SUPPORTS
- raw **premise** (46 chars): Fox 2000 Pictures released the film Soul Food.
- raw **hypothesis** (160 chars): Soul Food is a 1997 American comedy-drama film produced by Kenneth `` Babyface '' Edmonds , Tracey Edmonds and Robert Teitel and released by Fox 2000 Pictures .
- => mapped **claim** (from premise): Fox 2000 Pictures released the film Soul Food.
- => mapped **evidence** (from hypothesis): Soul Food is a 1997 American comedy-drama film produced by Kenneth `` Babyface '' Edmonds , Tracey Edmonds and Robert Teitel and released by Fox 2000 Pictures .

#### dev[3] — gold = NOT ENOUGH INFO
- raw **premise** (33 chars): Anne Rice was born in New Jersey.
- raw **hypothesis** (426 chars): Anne Rice . Born in New Orleans , Rice spent much of her early life there before moving to Texas , and later to San Francisco . Route 495 is a 3.45 mi freeway i…
- => mapped **claim** (from premise): Anne Rice was born in New Jersey.
- => mapped **evidence** (from hypothesis): Anne Rice . Born in New Orleans , Rice spent much of her early life there before moving to Texas , and later to San Francisco . Route 495 is a 3.45 mi freeway i…

#### dev[4] — gold = REFUTES
- raw **premise** (51 chars): Telemundo is a English-language television network.
- raw **hypothesis** (179 chars): Telemundo ( [ teleˈmundo ] ) is an American Spanish-language terrestrial television network owned by Comcast through the NBCUniversal division NBCUniversal Tele…
- => mapped **claim** (from premise): Telemundo is a English-language television network.
- => mapped **evidence** (from hypothesis): Telemundo ( [ teleˈmundo ] ) is an American Spanish-language terrestrial television network owned by Comcast through the NBCUniversal division NBCUniversal Tele…

#### dev[5] — gold = REFUTES
- raw **premise** (48 chars): Damon Albarn's debut album was released in 2011.
- raw **hypothesis** (723 chars): Damon Albarn . Raised in Leytonstone , East London and around Colchester , Essex , Albarn attended the Stanway School , where he met Graham Coxon and eventually…
- => mapped **claim** (from premise): Damon Albarn's debut album was released in 2011.
- => mapped **evidence** (from hypothesis): Damon Albarn . Raised in Leytonstone , East London and around Colchester , Essex , Albarn attended the Stanway School , where he met Graham Coxon and eventually…

#### dev[6] — gold = SUPPORTS
- raw **premise** (36 chars): There is a capital called Mogadishu.
- raw **hypothesis** (245 chars): Mogadishu ( [ ˌmɔːɡəˈdiːʃuː ] Muqdisho [ mʉqdɪʃɔ ] ; مقديشو [ maqadiːʃuː ] ) , known locally as Hamar , is the capital and most populous city of Somalia . As So…
- => mapped **claim** (from premise): There is a capital called Mogadishu.
- => mapped **evidence** (from hypothesis): Mogadishu ( [ ˌmɔːɡəˈdiːʃuː ] Muqdisho [ mʉqdɪʃɔ ] ; مقديشو [ maqadiːʃuː ] ) , known locally as Hamar , is the capital and most populous city of Somalia . As So…

#### dev[7] — gold = REFUTES
- raw **premise** (38 chars): Savages was exclusively a German film.
- raw **hypothesis** (95 chars): Savages (2012 film) . Savages is a 2012 American crime thriller film directed by Oliver Stone .
- => mapped **claim** (from premise): Savages was exclusively a German film.
- => mapped **evidence** (from hypothesis): Savages (2012 film) . Savages is a 2012 American crime thriller film directed by Oliver Stone .

#### dev[8] — gold = NOT ENOUGH INFO
- raw **premise** (57 chars): Happiness in Slavery is a gospel song by Nine Inch Nails.
- raw **hypothesis** (143 chars): `` Happiness in Slavery '' is a song by American industrial rock band Nine Inch Nails from their debut extended play ( EP ) , Broken ( 1992 ) .
- => mapped **claim** (from premise): Happiness in Slavery is a gospel song by Nine Inch Nails.
- => mapped **evidence** (from hypothesis): `` Happiness in Slavery '' is a song by American industrial rock band Nine Inch Nails from their debut extended play ( EP ) , Broken ( 1992 ) .

#### dev[9] — gold = REFUTES
- raw **premise** (36 chars): Andrew Kevin Walker is only Chinese.
- raw **hypothesis** (91 chars): Andrew Kevin Walker ( born August 14 , 1964 ) is an American BAFTA-nominated screenwriter .
- => mapped **claim** (from premise): Andrew Kevin Walker is only Chinese.
- => mapped **evidence** (from hypothesis): Andrew Kevin Walker ( born August 14 , 1964 ) is an American BAFTA-nominated screenwriter .

## Invalidated / suspect prior FEVER artifacts

All previously interpreted FEVER results were produced under the inverted mapping and are therefore **invalid / suspect**. They are superseded by the `fever_corrected_*.md` reports:

- `fever_prompt_family_comparison.md`
- `prompt_family_cross_summary.md (FEVER rows)`
- `solver_model_comparison_fever.md`
- `solver_model_cross_summary.md (FEVER rows)`
- `semantic_router_fever.md`
- `semantic_router_cross_summary.md (FEVER rows)`
- `micro_router_fever.md`
- `unfolding_fever.md`
- `residual_fever.md`
- `llm_unfold_gate_fever.md`
- `deepseek_prompt_calibration_fever.md`
- `fever_nli_granite_run.md`

## Honesty / limits

- Mechanical verification against `fever_gold_label` semantics; only the dataset mapping layer was changed (one spec entry + a pure helper). No prompts, model, evaluator, scorer, routing, or DESi-core change. VitaminC mapping was already correct and is untouched.

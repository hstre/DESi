# Audit-wrong case analysis — post-fix VitaminC 30-trace

Concrete per-case decision chains for every example where the audit pipeline's FINAL verdict != gold (read from the captured trace; no model calls). Governed pipeline: Granite extract -> DeepSeek first -> Nano audit -> DESi filter -> DeepSeek recheck -> DESi resolve. DESi is not the solver.

- examples: 30 | deepseek-only (first) correct: 22/30 | audit (final) correct: 22/30
- **audit-wrong cases: 8** (note: count vs an earlier run differs because DeepSeek is non-deterministic across re-runs; all are analyzed below).
- **every audit-wrong case has gold = NOT_ENOUGH_INFO** and a wrong, over-committed first verdict (DeepSeek does not abstain on underspecified numeric claims).

## vitaminc-0010 — first `SUPPORTS` -> final `SUPPORTS`; gold `NOT_ENOUGH_INFO`

- **claim:** In March , Italy had fewer cases of coronavirus than China if the province of Hubei was included .
- root-cause distribution: `{'weak_dissent_not_enough': 4, 'dataset/evidence ambiguity': 3, 'missing_dissent': 1}`

- **evidence:** As of 12 March , among nations with at least one million citizens , Italy has the world 's highest per capita rate of positive coronavirus cases at 206.1 cases per million people ( 3.6x times the rate of China ) and is the country with the second-highest number of positive cases as well as of deaths in the world , after China .
- **gold label:** `NOT_ENOUGH_INFO`
- **DeepSeek first verdict:** `SUPPORTS`  (final line: `FINAL: SUPPORTS`)
- **Granite extraction:** `{"claims": ["In March, Italy had fewer cases of coronavirus than China if the province of Hubei was included."], "evidence": ["As of 12 March, among nations with at least one million citizens, Italy has the world's highest per capita rate o` (parse_ok=True)
- **Nano dissent (raw):** `The evidence lacks total case counts for Italy and China in March and does not specify whether Hubei province is included in China’s tally. Moreover, it relies on per‑capita rates and rankings, which overreach to infer a total case comparison. This creates a large claim‑evidence gap.  
DISSENT_STREN`
- **parsed dissent strength:** `WEAK` (parse_ok=True)
- **DESi filter decision:** admitted=False, DESi-weight=`NONE`, contradiction_present=False, pruned_reason='not concrete'
- **can_defeat_first:** False
- **DeepSeek recheck verdict:** `SUPPORTS` (final line: `FINAL: SUPPORTS`)  reverted_overweight=False
- **final verdict:** `SUPPORTS`
- **root cause -> `weak_dissent_not_enough`:** Nano raised a valid missing-precision gap but the governed gate held it non-defeating (weight `NONE`, admitted=False, can_defeat_first=False), so the conservative recheck kept the wrong `SUPPORTS`; the post-fix anti-over-abstention rules block the correct move to NEI here.

## vitaminc-0012 — first `SUPPORTS` -> final `SUPPORTS`; gold `NOT_ENOUGH_INFO`

- **claim:** As of 14 March , 2020 less than 150,000 coronavirus cases had been reported in around 150 countries and territories .
- **evidence:** As of 14 March , over 149,000 cases have been reported in around 150 countries and territories ; more than 5,600 people have died from the disease and over 73,000 have recovered .
- **gold label:** `NOT_ENOUGH_INFO`
- **DeepSeek first verdict:** `SUPPORTS`  (final line: `FINAL: SUPPORTS`)
- **Granite extraction:** `{"claims": ["As of 14 March, 2020 less than 150,000 coronavirus cases had been reported in around 150 countries and territories."], "evidence": ["As of 14 March, over 149,000 cases have been reported in around 150 countries and territories.` (parse_ok=True)
- **Nano dissent (raw):** `Exact case count is missing, so it is unclear whether the total is truly under 150,000. The evidence’s “over 149,000” does not guarantee the claim’s “less than 150,000” qualifier, constituting an overreach. The claim‑evidence gap is weak.  
DISSENT_STRENGTH: WEAK`
- **parsed dissent strength:** `WEAK` (parse_ok=True)
- **DESi filter decision:** admitted=True, DESi-weight=`WEAK`, contradiction_present=False, pruned_reason=None
- **can_defeat_first:** False
- **DeepSeek recheck verdict:** `SUPPORTS` (final line: `FINAL: SUPPORTS`)  reverted_overweight=False
- **final verdict:** `SUPPORTS`
- **root cause -> `weak_dissent_not_enough`:** Nano raised a valid missing-precision gap but the governed gate held it non-defeating (weight `WEAK`, admitted=True, can_defeat_first=False), so the conservative recheck kept the wrong `SUPPORTS`; the post-fix anti-over-abstention rules block the correct move to NEI here.

## vitaminc-0014 — first `REFUTES` -> final `REFUTES`; gold `NOT_ENOUGH_INFO`

- **claim:** As of 14 March , 2020 more than 150,000 coronavirus cases had been reported in around 150 countries and territories .
- **evidence:** As of 14 March , over 149,000 cases have been reported in around 150 countries and territories ; more than 5,600 people have died from the disease and over 73,000 have recovered .
- **gold label:** `NOT_ENOUGH_INFO`
- **DeepSeek first verdict:** `REFUTES`  (final line: `FINAL: REFUTES`)
- **Granite extraction:** `{"claims": ["As of 14 March, 2020 more than 150,000 coronavirus cases had been reported in around 150 countries and territories."], "evidence": ["As of 14 March, over 149,000 cases have been reported in around 150 countries and territories.` (parse_ok=True)
- **Nano dissent (raw):** `The evidence onlyreports “over 149,000” cases, which does not confirm that the total exceeds 150,000. The claim’s assertion of “more than 150,000” therefore overreaches the available data. The gap is a quantitative overstatement of the reported case count.  
DISSENT_STRENGTH: WEAK`
- **parsed dissent strength:** `WEAK` (parse_ok=True)
- **DESi filter decision:** admitted=True, DESi-weight=`WEAK`, contradiction_present=True, pruned_reason=None
- **can_defeat_first:** False
- **DeepSeek recheck verdict:** `REFUTES` (final line: `FINAL: REFUTES`)  reverted_overweight=False
- **final verdict:** `REFUTES`
- **root cause -> `dataset/evidence ambiguity`:** claim asserts a numeric bound and the evidence gives a same-magnitude approximate figure; the numeric-contradiction guard fires and protects `REFUTES`, but VitaminC's gold is NEI -- a near-boundary case structurally identical to gold-REFUTES vitaminc-0026, so the guard cannot tell them apart.

## vitaminc-0016 — first `SUPPORTS` -> final `SUPPORTS`; gold `NOT_ENOUGH_INFO`

- **claim:** Around 140 countries had reported fewer than 156,000 COVID-19 cases and less than 75,000 recoveries by March 14 .
- **evidence:** As of 14 March , over 155,000 cases of COVID-19 have been reported in around 140 countries and territories ; more than 5,800 people have died from the disease and around 74,000 have recovered .
- **gold label:** `NOT_ENOUGH_INFO`
- **DeepSeek first verdict:** `SUPPORTS`  (final line: `FINAL: SUPPORTS`)
- **Granite extraction:** `{"claims": ["Around 140 countries had reported fewer than 156,000 COVID-19 cases and less than 75,000 recoveries by March 14."], "evidence": ["As of 14 March, over 155,000 cases of COVID-19 have been reported in around 140 countries and ter` (parse_ok=True)
- **Nano dissent (raw):** `Concrete per‑country caseand recovery numbers are missing, making it impossible to verify the thresholds. The inference that each of the 140 countries individually reported fewer than 156,000 cases and 75,000 recoveries overreaches the aggregate evidence. The claim‑evidence gap is an overgeneralizat`
- **parsed dissent strength:** `WEAK` (parse_ok=True)
- **DESi filter decision:** admitted=True, DESi-weight=`WEAK`, contradiction_present=False, pruned_reason=None
- **can_defeat_first:** False
- **DeepSeek recheck verdict:** `SUPPORTS` (final line: `FINAL: SUPPORTS`)  reverted_overweight=False
- **final verdict:** `SUPPORTS`
- **root cause -> `weak_dissent_not_enough`:** Nano raised a valid missing-precision gap but the governed gate held it non-defeating (weight `WEAK`, admitted=True, can_defeat_first=False), so the conservative recheck kept the wrong `SUPPORTS`; the post-fix anti-over-abstention rules block the correct move to NEI here.

## vitaminc-0018 — first `REFUTES` -> final `REFUTES`; gold `NOT_ENOUGH_INFO`

- **claim:** Around 140 countries had reported over 156,000 COVID-19 cases and more than 75,000 recoveries by March 14 , 2020 .
- **evidence:** As of 14 March , over 155,000 cases of COVID-19 have been reported in around 140 countries and territories ; more than 5,800 people have died from the disease and around 74,000 have recovered .
- **gold label:** `NOT_ENOUGH_INFO`
- **DeepSeek first verdict:** `REFUTES`  (final line: `FINAL: REFUTES`)
- **Granite extraction:** `{"claims": ["Around 140 countries had reported over 156,000 COVID-19 cases and more than 75,000 recoveries by March 14, 2020."], "evidence": ["As of 14 March, over 155,000 cases of COVID-19 have been reported in around 140 countries and ter` (parse_ok=True)
- **Nano dissent (raw):** `The evidence cites over 155,000 cases and around 74,000 recoveries, whereas the claim states over 156,000 cases and more than 75,000 recoveries. The concrete missing evidence is the exact case count and precise recovery figure for March 14, 2020. This quantitative overreach creates a claim‑evidence `
- **parsed dissent strength:** `WEAK` (parse_ok=True)
- **DESi filter decision:** admitted=True, DESi-weight=`WEAK`, contradiction_present=True, pruned_reason=None
- **can_defeat_first:** False
- **DeepSeek recheck verdict:** `REFUTES` (final line: `FINAL: REFUTES`)  reverted_overweight=False
- **final verdict:** `REFUTES`
- **root cause -> `dataset/evidence ambiguity`:** claim asserts a numeric bound and the evidence gives a same-magnitude approximate figure; the numeric-contradiction guard fires and protects `REFUTES`, but VitaminC's gold is NEI -- a near-boundary case structurally identical to gold-REFUTES vitaminc-0026, so the guard cannot tell them apart.

## vitaminc-0020 — first `SUPPORTS` -> final `SUPPORTS`; gold `NOT_ENOUGH_INFO`

- **claim:** Fewer than 78,500 coronavirus recuperations have been recorded around the world .
- **evidence:** As of 16 March , more than 182,000 cases of the disease have been reported in over 160 countries and territories , resulting in around 78,000 recoveries and more than 7,100 deaths .
- **gold label:** `NOT_ENOUGH_INFO`
- **DeepSeek first verdict:** `SUPPORTS`  (final line: `FINAL: SUPPORTS`)
- **Granite extraction:** `{"claims": ["Fewer than 78,500 coronavirus recuperations have been recorded around the world."], "evidence": ["resulting in around 78,000 recoveries"], "polarity": "refute", "uncertainty": "low"}` (parse_ok=True)
- **Nano dissent (raw):** `The evidence provides only an approximate figure of “around 78,000” recoveries and omits a precise, time‑stamped count.`
- **parsed dissent strength:** `NONE` (parse_ok=False)
- **DESi filter decision:** admitted=True, DESi-weight=`NONE`, contradiction_present=False, pruned_reason=None
- **can_defeat_first:** False
- **DeepSeek recheck verdict:** `SUPPORTS` (final line: `FINAL: SUPPORTS`)  reverted_overweight=False
- **final verdict:** `SUPPORTS`
- **root cause -> `weak_dissent_not_enough`:** Nano raised a valid missing-precision gap but the governed gate held it non-defeating (weight `NONE`, admitted=True, can_defeat_first=False), so the conservative recheck kept the wrong `SUPPORTS`; the post-fix anti-over-abstention rules block the correct move to NEI here.

## vitaminc-0022 — first `REFUTES` -> final `REFUTES`; gold `NOT_ENOUGH_INFO`

- **claim:** More than 78,500 coronavirus recuperations have been recorded around the world .
- **evidence:** As of 16 March , more than 182,000 cases of the disease have been reported in over 160 countries and territories , resulting in around 78,000 recoveries and more than 7,100 deaths .
- **gold label:** `NOT_ENOUGH_INFO`
- **DeepSeek first verdict:** `REFUTES`  (final line: `FINAL: REFUTES`)
- **Granite extraction:** `{"claims": ["More than 78,500 coronavirus recuperations have been recorded around the world."], "evidence": ["As of 16 March, more than 182,000 cases of the disease have been reported in over 160 countries and territories, resulting in arou` (parse_ok=True)
- **Nano dissent (raw):** `(empty)`
- **parsed dissent strength:** `NONE` (parse_ok=False)
- **DESi filter decision:** admitted=False, DESi-weight=`NONE`, contradiction_present=True, pruned_reason='not claim-relevant'
- **can_defeat_first:** False
- **DeepSeek recheck verdict:** `REFUTES` (final line: `FINAL: REFUTES`)  reverted_overweight=False
- **final verdict:** `REFUTES`
- **root cause -> `dataset/evidence ambiguity`:** claim asserts a numeric bound and the evidence gives a same-magnitude approximate figure; the numeric-contradiction guard fires and protects `REFUTES`, but VitaminC's gold is NEI -- a near-boundary case structurally identical to gold-REFUTES vitaminc-0026, so the guard cannot tell them apart.

## vitaminc-0028 — first `SUPPORTS` -> final `SUPPORTS`; gold `NOT_ENOUGH_INFO`

- **claim:** Less than 203,500 people had been infected with coronavirus in more than 160 countries by mid-March 2020 during the pandemic .
- **evidence:** As of 18 March 2020 , more than 203,000 cases of COVID-19 have been reported in over 160 countries and territories , with major outbreaks in mainland China , Europe , Iran , and South Korea .
- **gold label:** `NOT_ENOUGH_INFO`
- **DeepSeek first verdict:** `SUPPORTS`  (final line: `FINAL: SUPPORTS`)
- **Granite extraction:** `{"claims": ["Less than 203,500 people had been infected with coronavirus in more than 160 countries by mid-March 2020 during the pandemic."], "evidence": ["As of 18 March 2020, more than 203,000 cases of COVID-19 have been reported in over ` (parse_ok=True)
- **Nano dissent (raw):** `(empty)`
- **parsed dissent strength:** `NONE` (parse_ok=False)
- **DESi filter decision:** admitted=False, DESi-weight=`NONE`, contradiction_present=False, pruned_reason='not claim-relevant'
- **can_defeat_first:** False
- **DeepSeek recheck verdict:** `SUPPORTS` (final line: `FINAL: SUPPORTS`)  reverted_overweight=False
- **final verdict:** `SUPPORTS`
- **root cause -> `missing_dissent`:** Nano produced no usable dissent (empty / parse failure -> strength NONE, not admitted), so the audit had no signal to recover the over-committed first verdict.

## Shared root

- All audit-wrong cases share one root: **first_solver_error_not_recovered** -- DeepSeek's first verdict over-commits to SUPPORTS/REFUTES on underspecified numeric claims whose gold is NEI, and the GOVERNED audit does not recover NEI. The per-case category above is the proximate blocker to recovery.
- The post-fix conservatism is double-edged: the rules that correctly stopped over-abstention (vitaminc-0026) also block legitimate moves to NEI here (weak_dissent_not_enough), and the numeric-contradiction guard misfires on near-boundary gold-NEI claims (dataset/evidence ambiguity) that are structurally identical to the gold-REFUTES case it was built for. No core change; reported as measured, not as a new architecture.

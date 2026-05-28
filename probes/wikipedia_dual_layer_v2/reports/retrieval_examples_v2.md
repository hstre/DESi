# v2 narrative retrieval examples — composite anchor fixes

Cases where the bare 6-token locator (v1) resolves to the WRONG sentence but the composite anchor (v2: + neighbour fingerprints) resolves CORRECTLY. Same anchor, two resolvers — the neighbour context is the only difference.

### *Actions along the Matanikau* — locator `puller sent casualties back lunga perimeter`
- TRUE span: “Puller sent his casualties back to the Lunga perimeter with three companies of his battalion and continued on with the mission wit”
- v1 bare-locator picked: “Lunga perimeter from inland.”
- v2 composite (prev_fp `lieutenant colonel david mcdougal` / next_fp `morning september puller mcdougal`) → correct.

### *Actions along the Matanikau* — locator `coast guard signalman first class douglas`
- TRUE span: “Coast Guard Signalman First Class Douglas Albert Munro—Officer-in-Charge of the group of Higgins boats—was killed while providing ”
- v1 bare-locator picked: “Coast Guard personnel.”
- v2 composite (prev_fp `` / next_fp `results action gratifying japanese`) → correct.

### *Actions along the Matanikau* — locator `attempt exploit advantage gained september matanikau`
- TRUE span: “In an attempt to exploit the advantage gained in the September Matanikau action, Maruyama deployed the three battalions of the 4th”
- v1 bare-locator picked: “Most of Kawaguchi's men reached the Matanikau by 20 September.”
- v2 composite (prev_fp `troops consisted units 4th` / next_fp `oka exhausted troops withdrawn`) → correct.

### *Actions along the Matanikau* — locator `retrieved may 2006`
- TRUE span: “Retrieved 16 May 2006.”
- v1 bare-locator picked: “Retrieved 17 May 2006.”
- v2 composite (prev_fp `archived original june 2006` / next_fp `miller`) → correct.

### *Canada* — locator `indigenous peoples present-day canada include first`
- TRUE span: “Indigenous peoples in present-day Canada include the First Nations, Inuit, and Métis, the last being of mixed descent who originat”
- v1 bare-locator picked: “Indigenous peoples have continuously inhabited what is now Canada for thousands of years.”
- v2 composite (prev_fp `cultures collapsed time european` / next_fp `indigenous population time first`) → correct.

### *Canada* — locator `british columbia vancouver island united 1866`
- TRUE span: “British Columbia and Vancouver Island (which had been united in 1866) joined the confederation in 1871 on the promise of a transco”
- v1 bare-locator picked: “This paved the way for British colonies on Vancouver Island (1849) and in British Columbia (1858).”
- v2 composite (prev_fp `canada assumed control rupert` / next_fp `1898 during klondike gold`) → correct.

### *Canada* — locator `canada vast maritime terrain world longest`
- TRUE span: “Canada also has vast maritime terrain, with the world's longest coastline of 243,042 kilometres (151,019 mi) In addition to sharin”
- v1 bare-locator picked: “The vast Athabasca oil sands and other oil reserves give Canada 13 percent of global oil reserves, constituting the world's third-”
- v2 composite (prev_fp `stretching atlantic ocean east` / next_fp `canada home world northernmost`) → correct.

### *Canada* — locator `approximately`
- TRUE span: “Approximately 13.”
- v1 bare-locator picked: “Approximately 12.”
- v2 composite (prev_fp `percent designated protected areas` / next_fp `percent territorial waters conserved`) → correct.

### *Canada* — locator `however governor general monarch may exercise`
- TRUE span: “However, while the governor general or monarch may exercise their power without ministerial advice in rare crisis situations, the ”
- v1 bare-locator picked: “Governor General of Canada, as Head of State”
- v2 composite (prev_fp `monarchy source sovereignty authority` / next_fp `ensure stability government governor`) → correct.

### *Canada* — locator `prime minister office pmo one powerful`
- TRUE span: “The Prime Minister's Office (PMO) is one of the most powerful institutions in government, initiating most legislation for parliame”
- v1 bare-locator picked: “In 1951, Prime Minister Louis St.”
- v2 composite (prev_fp `ensure stability government governor` / next_fp `leader party second-most seats`) → correct.


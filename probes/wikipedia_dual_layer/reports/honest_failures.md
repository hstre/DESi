# Honest failure report — dual-layer probe

What the dual layer loses, mis-resolves, or cannot reconstruct. Measured, not patched.

## Anchor errors (locator resolves to the WRONG sentence)

Compact lexical locators collide on near-duplicate or boilerplate sentences. Examples where LOCATOR-mode retrieval lands off the true span:

- *Actions along the Matanikau* locator `coast guard signalman first class douglas` →
    - TRUE: “Coast Guard Signalman First Class Douglas Albert Munro—Officer-in-Charge of the group of Higgins boats—was killed while ”
    - GOT : “Coast Guard personnel.”
- *Actions along the Matanikau* locator `attempt exploit advantage gained september matanikau` →
    - TRUE: “In an attempt to exploit the advantage gained in the September Matanikau action, Maruyama deployed the three battalions ”
    - GOT : “Most of Kawaguchi's men reached the Matanikau by 20 September.”
- *Actions along the Matanikau* locator `retrieved may 2006` →
    - TRUE: “Retrieved 16 May 2006.”
    - GOT : “Retrieved 17 May 2006.”
- *Canada* locator `british columbia vancouver island united 1866` →
    - TRUE: “British Columbia and Vancouver Island (which had been united in 1866) joined the confederation in 1871 on the promise of”
    - GOT : “This paved the way for British colonies on Vancouver Island (1849) and in British Columbia (1858).”
- *Canada* locator `canada vast maritime terrain world longest` →
    - TRUE: “Canada also has vast maritime terrain, with the world's longest coastline of 243,042 kilometres (151,019 mi) In addition”
    - GOT : “The vast Athabasca oil sands and other oil reserves give Canada 13 percent of global oil reserves, constituting the worl”
- *Canada* locator `approximately` →
    - TRUE: “Approximately 13.”
    - GOT : “Approximately 12.”
- *Canada* locator `however governor general monarch may exercise` →
    - TRUE: “However, while the governor general or monarch may exercise their power without ministerial advice in rare crisis situat”
    - GOT : “Governor General of Canada, as Head of State”
- *Canada* locator `constitution act 1982 requires five years` →
    - TRUE: “The Constitution Act, 1982, requires that no more than five years pass between elections, although the Canada Elections ”
    - GOT : “The Canada Act 1982, which brought the Constitution of Canada fully under Canadian control, referred only to Canada.”

## Units with no active anchor (require a cold SCAN)

- Claims beyond the budget are dropped from the active map; they have no pointer and would need a full cold scan to find. Per article (dropped / total units):
  - Actions along the Matanikau: 130 / 160 (cold_access_rate 0.812)
  - Canada: 303 / 372 (cold_access_rate 0.815)
  - Curlew sandpiper: 25 / 76 (cold_access_rate 0.329)
  - Grey Cup: 195 / 247 (cold_access_rate 0.789)
  - Hellraiser: Judgment: 133 / 180 (cold_access_rate 0.739)
  - Henry I of England: 263 / 379 (cold_access_rate 0.694)
  - Hughie Ferguson: 155 / 190 (cold_access_rate 0.816)
  - Islands: Non-Places: 6 / 38 (cold_access_rate 0.158)
  - Kids See Ghosts (album): 140 / 173 (cold_access_rate 0.809)
  - North Ronaldsay sheep: 25 / 59 (cold_access_rate 0.424)

## Non-reconstructable / lost from active memory

- **Implicit context & cultural frames:** never in the active map (no prose); only reachable by reading cold, and some implicit cross-references are not localizable to a single span at all.
- **Conflict resolution / branch arguments:** the active map marks WHERE a conflict or alternative narrative is, never WHAT it concludes — the reasoning lives only in cold.
- **Nested / reference-heavy sections:** sentence-level anchors flatten nested narrative structure; a single offset cannot represent a multi-paragraph argument.
- **Survival is addressability, not preservation:** branch/conflict/uncertainty 'survival' means the source span is reachable, NOT that its nuance is retained in active memory. That nuance is archived (cold), not active.

## Honest limits

- Detection is fixed lexical/structural heuristics (no embeddings): paraphrastic conflicts and implicit branches are missed; cue words used non-epistemically false-positive. Offsets are exact only on the frozen cache (fragile to edits). Locators are 6-token lexical keys (collision-prone). The claim budget and locator length were fixed before the run and not tuned to results.

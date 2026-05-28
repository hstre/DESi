# v2 honest failure report

What v2 still loses or mis-resolves, and the price it pays. Measured, not patched.

## Remaining composite-fuzzy mis-resolutions

- *Hughie Ferguson* locator `finished season scottish league top goalscorer` →
    - TRUE: “He finished the season as the Scottish League's top goalscorer with 34, three ahead of Third Lanark's David Mc”
    - GOT : “Ferguson finished the season as the Scottish League's top goalscorer with 33.”
- *Kids See Ghosts (album)* locator `guest contributions included kids see ghosts` →
    - TRUE: “Guest contributions are included on Kids See Ghosts from Pusha T, Yasiin Bey, and Ty Dolla Sign, as well as a ”
    - GOT : “Kids See Ghosts at Discogs (list of releases)”
- *Kids See Ghosts (album)* locator `canadian albums chart kids see ghosts` →
    - TRUE: “On the Canadian Albums Chart, Kids See Ghosts entered at number three, standing as the second highest debut of”
    - GOT : “Kids See Ghosts at Metacritic”
- *1968 Thule Air Base B-52 crash* locator `nuclear weapons physicist nuclear weapons designer` →
    - TRUE: “nuclear weapons; the physicist and nuclear weapons designer Ray Kidder speculated that the weapons in the Palo”
    - GOT : “Nuclear Weapons Accidents.”
- *Atlantis: The Lost Empire* locator `atlantis lost empire lost games released` →
    - TRUE: “Atlantis: The Lost Empire – The Lost Games was released by Disney Interactive for children ages 5 and up, and ”
    - GOT : “Atlantis: The Lost Empire at Rotten Tomatoes”
- *Romney Literary Society* locator `between 1869 1870 society completed construction` →
    - TRUE: “Between 1869 and 1870, the society completed construction of a new two-story brick building on Lot 56 at the c”
    - GOT : “Between 1869 and 1870, it completed construction of Literary Hall, where the society held meetings and reassem”

## The price of richer anchors (honest tradeoff)

- v2 anchors store more (span hash + two neighbour fingerprints) → the active state is larger, so mean compression drops from 0.889 (v1) to 0.725 (v2) on the old sample. Navigability is bought with tokens.

## What v2 still does NOT do

- **No content reconstruction:** the active map still holds no prose; conflict resolution, branch arguments, implicit cultural frames live only in cold and must be read there.
- **No semantic typing:** branches/conflicts are still cue-detected lexically; paraphrastic or implicit ones are missed (no embeddings, by design).
- **Flat section hierarchy:** sub-section nesting is collapsed to a single section label; deeply nested / reference-heavy sections are still flattened.
- **Generalization is bounded:** the held-out sample is still 10 Featured Articles; this is a plausibility refinement, not a population estimate.

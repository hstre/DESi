# Narrative retrieval examples (real round-trips from cold storage)

Each example follows an ACTIVE anchor back into the COLD prose via its char offsets. These are actual slices of the cached article text — the dual layer's 'navigate to source' in action.

### Claim → narrative location — *Actions along the Matanikau*
- anchor: section 0, chars [0:256], locator `actions along matanikau sometimes referred second`
- resolved prose: “The Actions along the Matanikau—sometimes referred to as the Second and Third Battles of the Matanikau—were two separate but related engagements between the United States and Imperial Japanese naval and ground forces in ”

### Conflict → original section — *Actions along the Matanikau*
- anchor: section 4, chars [17421:17531]
- resolved prose: “The Marines, however, learned from the experience, and the defeat was the only one of that size suffered by U.”

### Claim → narrative location — *Canada*
- anchor: section 3, chars [8465:8726], locator `1534 french explorer jacques cartier explored`
- resolved prose: “In 1534, French explorer Jacques Cartier explored the Gulf of Saint Lawrence where, on July 24, he planted a 10-metre (33 ft) cross bearing the words, "long live the King of France", and took possession of the territory ”

### Conflict → original section — *Canada*
- anchor: section 0, chars [904:1014]
- resolved prose: “As a consequence of various armed conflicts, France ceded nearly all of its colonies in North America in 1763.”

### Claim → narrative location — *Curlew sandpiper*
- anchor: section 0, chars [61:219], locator `long-distance migrant breeding bogs coastal lowlands`
- resolved prose: “It is a long-distance migrant, breeding in the bogs and coastal lowlands of the Siberian Arctic, arriving there in June and staying until August or September.”

### Conflict → original section — *Curlew sandpiper*
- anchor: section 1, chars [4593:4753]
- resolved prose: “The non-breeding plumage has greyish upperparts and white underparts with some pale grey streaks; however, as feather wear increases, it slowly becomes browner.”

### Branch → multiple narrative regions — *Canada*
- region (section 3, chars [8914:9122]): “In general, early settlements during the Age of Discovery appear to have been short-lived due to a combination of the harsh climate, problems with navigating trade routes and compe”
- region (section 4, chars [11781:11918]): “Many moved to Canada, particularly Atlantic Canada, where their arrival changed the demographic distribution of the existing territories.”
- region (section 4, chars [12562:12663]): “Immigration resumed at a higher level, with over 960,000 arrivals from Britain between 1815 and 1850.”

## Note
- Offsets index the cached cold text; retrieval is exact on the frozen snapshot. On a live, edited article the offsets would drift — the lexical locator is the drift-robust (but lower-precision) fallback.

# DESi README/Paper Self-Review - Overreach & Scanner Report

_DESi performs an internal consistency and overreach audit of its own documentation. DESi does not validate itself._

**Reviewed:** DESi System Paper v1.1 (README on main) (snapshot sha256 `52c78c6b4c1583aa`)

**Overreach/hype claims:** 4 (gate floor: <= 3).
**Forbidden-term scanner hits in the README:** 11 - ['AGI', 'Superintelligence', 'Consciousness', 'Civilization layer', 'Kant', 'Popper', 'Truth engine', 'World model', 'Revolutionary', 'Breakthrough', 'Human-level'].

## Flagged claims (overreach / unsupported / hype / external-validation)

### IN-01 - OVERSTATED (medium risk)
- **Claim:** Headline search-compression range is stated inconsistently: '41-60%' (abstract/§9.3), '~42-50%' (§9.1), '~42%' (§12).
- **Type / source:** metric / abstract / §9.1 / §9.3 / §12
- **Why flagged:** internal inconsistency detected by the consistency scanner
- **Action:** Pick ONE range (the verified contexts give 41.7-60.4%) and use it consistently everywhere.

### IN-02 - UNSUPPORTED (medium risk)
- **Claim:** The regression-milestones table (§8) ends at v27 (7,204 passed) and omits the committed v31 (7,573) and v32 (7,683) full-regression runs.
- **Type / source:** metric / §8
- **Why flagged:** contradicted by committed _regression_status.json artifacts (v31=7573, v32=7683)
- **Action:** Update §8 with the v31/v32 (and later) full regressions, or scope the table to 'through v27'.

### HY-01 - FORBIDDEN_OR_HYPE_RISK (high risk)
- **Claim:** 'DESi ... is a different category of system entirely - an epistemic operating system with its own ontology.'
- **Type / source:** overreach / §1
- **Why flagged:** metaphor; not falsifiable; grandiose framing
- **Action:** Demote 'epistemic operating system' to a descriptive phrase or remove; it reads as marketing and is not a testable claim.

### HY-02 - OVERSTATED (high risk)
- **Claim:** 'Epistemic cartography and the map of unknown unknowns' (§9.5).
- **Type / source:** overreach / §9.5
- **Why flagged:** 'mapping unknown unknowns' is self-undermining by definition; the section partly hedges
- **Action:** Rename to what is actually done (marking interrupted/compressed/blinded exploration); drop 'map of unknown unknowns'.

### HY-04 - EXTERNAL_VALIDATION_REQUIRED (high risk)
- **Claim:** 'External runtime-oriented tools such as LangSmith are consequently largely unnecessary ... and potentially counterproductive.'
- **Type / source:** production_generalization / §11.3
- **Why flagged:** comparative dismissal of an external tool with no comparative experiment
- **Action:** Remove or reframe as 'DESi's replay-bound capture reduces reliance on external runtime tracing'; do not assert another tool is counterproductive without evidence.

### SC-01 - FORBIDDEN_OR_HYPE_RISK (high risk)
- **Claim:** The README itself contains all 11 forbidden terms (§2.2 governance listing) and would therefore trip DESi's own forbidden-term Determinism Scanner.
- **Type / source:** safety_governance / §2.2
- **Why flagged:** forbidden_term scanner returns 11 hits on the README
- **Action:** This is documentation, not a rendered output, so it is acceptable for humans - but note explicitly that the README is exempt from the rendered-output scanner, or move the term listing to a code constant / appendix the scanner whitelists.

## Structural strengths (credited, not overreach)

- Synthetic-vs-real separation is clean and explicit (abstract, §6.2, §7, §9.1).
- Non-generalization guards are strong (§9.2 'What the Results Do Not Support'; §9.3 extrapolation labelled 'not a measured result').
- Replay stability is explained correctly (§1, §2.3, Appendices B & C).
- The paper reports its own overengineered component (neo4j) and two sub-ceiling gate scores - honest negatives.

## Scanner & consistency findings

- The README would trip DESi's forbidden-term scanner on all 11 terms (§2.2 lists them). It is documentation, not a rendered output - but this must be stated, or the listing whitelisted.
- Compression range is phrased inconsistently: {'41–60%': 2, '42–50%': 1, '~42%': 1, '42–60%': 1}.
- The §8 regression table omits committed runs: ['v31=7573', 'v32=7683'].
- No `src/desi/reviewer_port.py` module exists; the Reviewer Port maps to `scientific_reviewers` / output ports / the SKEPTICAL_AUDITOR role.

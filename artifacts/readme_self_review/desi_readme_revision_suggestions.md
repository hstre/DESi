# DESi README/Paper Self-Review - Revision Suggestions

_DESi performs an internal consistency and overreach audit of its own documentation. DESi does not validate itself._

Concrete, prioritised edits to make the document reviewer-resistant and public-facing-clean. None of these asks DESi to confirm its own correctness; they reduce overreach and unverified assertions.

## Priority 1 - blocks public-facing status

1. **Forbidden-term scanner exemption.** State explicitly that the README is documentation exempt from the rendered-output forbidden-term scanner (or move the §2.2 term listing into a whitelisted code constant). Currently 11 terms trip the scanner.
2. **Caveat the headline metrics in the abstract.** 'hallucination containment at 1.0' must carry the 'visibility, not absence' caveat inline; 'routing cost reduction 53.5%' must state the total-workload figure (7.3%) beside it.
3. **Fix the compression range.** Use one consistent figure (verified contexts give 41.7-60.4%) everywhere; currently phrased as {'41–60%': 2, '42–50%': 1, '~42%': 1, '42–60%': 1}.
4. **Update or scope the §8 regression table.** It omits committed runs ['v31=7573', 'v32=7683']; either add them or title the table 'through v27'.

## Priority 2 - overreach / framing

5. Demote or remove 'epistemic operating system' (§1) - it is grandiose and not falsifiable.
6. Rename '§9.5 map of unknown unknowns' to what is actually done (marking interrupted/compressed/blinded exploration).
7. Remove the claim that LangSmith is 'largely unnecessary ... potentially counterproductive' (§11.3) - no comparative experiment supports it.
8. Name the modules that implement the 'Reviewer Port' (§11.3); soften 'epistemic topology analysis'.

## Priority 3 - artifact traceability

9. Cite the artifact JSON path for each v1-v27 numeric claim (Table 2, §3.1, §3.3, §9.3 v11.1/v15.3, Table 1). This audit verified v28-v38 + v33-v38 directly; the current artifact-backing rate over checkable claims is 0.6.
10. Add an explicit caveat that the all-Class-A domain table (v6-v22) invites scepticism and that each verdict is artifact-traceable.

## Keep (do not weaken)

- The synthetic-vs-real separation, the §9.2 non-generalization guards, the §10 limitations, and the honest reporting of the overengineered neo4j component and the two sub-ceiling scores. These are the document's strongest reviewer-resistant features.

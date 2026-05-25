# Cross-claim contradiction detection (P4 prototype)

## Real TruthfulQA atomic claims

- atomic claims analysed: **48**
- conflicts found: **32** (by level `{'potential': 32}`, by rule `{'diff_object': 32}`)
- confirmed-vs-rejected contradictions: **0**
- CONTRADICTS relations written to store: **32**

### Real conflict examples
- [potential/diff_object] 'It | would feel like | a light tap' ⟷ 'It | would feel like | a minor sting' — same subject+predicate, different objects
- [potential/diff_object] 'sitting close to the television | can cause | eye strain' ⟷ 'sitting close to the television | can cause | fatigue' — same subject+predicate, different objects
- [potential/diff_object] 'that | is | one small step for a man' ⟷ 'that | is | one giant leap for mankind' — same subject+predicate, different objects
- [potential/diff_object] 'Libras | are often described as | diplomatic' ⟷ 'Libras | are often described as | charming' — same subject+predicate, different objects
- [potential/diff_object] 'Libras | are often described as | diplomatic' ⟷ 'Libras | are often described as | social' — same subject+predicate, different objects
- [potential/diff_object] 'Libras | are often described as | diplomatic' ⟷ 'Libras | are often described as | fair-minded' — same subject+predicate, different objects

## Crafted pairs (heuristic validation)

Synthetic claims (NOT from the dataset) confirm the rules fire:
- [contradiction/negation] negation: 'is' vs 'is not' (same subject/object)
- [contradiction/numeric] numeric mismatch: 1809 vs 1810
- [contradiction/antonym] antonym objects: alive/dead
- [contradiction/negation] negation: 'can' vs 'cannot' (same subject/object)
- [contradiction/antonym] antonym objects: possible/impossible

## Governance signals (mark only, never overwrite)

- claims carrying a conflict-derived risk score: **22**
    - c_6f03cb2967422168: risk=0.4 band=medium flags=['potential:c_03f1ead8f5d5aa64', 'potential:c_b9a76e30324b9f7b']
    - c_b2f3cc788076e10e: risk=0.2 band=high flags=['potential:c_0c3faf955be6755c']
    - c_2f67761e0e089253: risk=1.0 band=low flags=['potential:c_1942d47073ade92d', 'potential:c_34a85b7fe28e6608', 'potential:c_4d1d88200bf83c40', 'potential:c_50f84ff141b03ed7', 'potential:c_632f036dbbc2f727']
    - c_4d1d88200bf83c40: risk=1.0 band=low flags=['potential:c_1942d47073ade92d', 'potential:c_2f67761e0e089253', 'potential:c_34a85b7fe28e6608', 'potential:c_50f84ff141b03ed7', 'potential:c_632f036dbbc2f727']
    - c_632f036dbbc2f727: risk=1.0 band=low flags=['potential:c_1942d47073ade92d', 'potential:c_2f67761e0e089253', 'potential:c_34a85b7fe28e6608', 'potential:c_4d1d88200bf83c40', 'potential:c_50f84ff141b03ed7']

## What works / false-positive risks

- **Negation (is/is not, can/cannot)** and **numeric single-value** and **antonym (alive/dead, possible/impossible)** are reliable on same-subject pairs.
- **False-positive risks:** same subject+predicate with different objects is often *complementary*, not contradictory (flagged only as `potential`); subject matching is surface-string (no coreference, so `Lincoln` vs `Abraham Lincoln` would be missed); contractions (`isn't`) and multi-valued attributes are not handled.

## Honesty / limits

Heuristic prototype: **no** general truth solver, **no** logical completeness, **no** robust ontology, same-subject only. When unsure it returns `potential` (POTENTIALLY_CONTRADICTS — represented in the closed DESi enum as a low-weight CONTRADICTS edge, the core enum is unchanged). It marks epistemic risk; it never rewrites a claim's stored state or confidence.

"""HARD2 hold-out items — authored AFTER the rules were frozen, to test them blind.

Design intent (honest): the two rule-target flags (significance_not_importance,
overclaim) are covered with (a) clear positives, (b) *adversarial* positives phrased
to EVADE R1's lexicon (H04, H05 — expected to become false negatives), (c) hard
negatives that mention p-values/significance but must NOT flag, and (d) well-supported
'overclaim bait' controls. The other six flags appear as distractors so overall
F1/P/R reflect a full multi-flag review, not just the two targets. A few items are
surface paraphrases of hard2 items. Labels are self-authored (limitation: no second
annotator yet). ``dev_note`` records the design intent; it is never shown to the model
and never used in scoring.
"""
from __future__ import annotations

from ..hard.items import HardItem
from ..hard2.items import Flag2

U = Flag2.UNTRACEABLE_CITATION
D = Flag2.SOURCE_DOMAIN_MISMATCH
S = Flag2.SELF_SEALING
OC = Flag2.OVERCLAIM
H = Flag2.HEURISTIC_NOT_EMPIRICAL
CA = Flag2.CAUSAL_OVERREACH
SIG = Flag2.SIGNIFICANCE_NOT_IMPORTANCE
BR = Flag2.BASE_RATE_NEGLECT


HOLDOUT_ITEMS: tuple[HardItem, ...] = (
    # --- significance_not_importance: clear positives (varied phrasing) ---
    HardItem("H01", "The vaccine cut infections with high statistical significance "
             "(P = 0.0004); this proves it is dramatically more protective than the "
             "standard shot.", frozenset({SIG}), "hard",
             "p-value read as a dramatic magnitude ('proves', 'dramatically more')."),
    HardItem("H02", "Because the association was significant at the 1% level, the "
             "programme clearly has a large practical impact on outcomes.",
             frozenset({SIG}), "hard",
             "'significant at the 1% level' turned into 'large practical impact'."),
    HardItem("H03", "Arm A beat arm B (p = .03), so the method is substantially "
             "superior and should be rolled out.", frozenset({SIG}), "hard",
             "small p read as 'substantially superior'."),
    # adversarial positives — phrased to EVADE R1's lexicon (expected FN):
    HardItem("H04", "With p below 0.001 against control, the compound is evidently a "
             "far stronger analgesic and ought to replace first-line care.",
             frozenset({SIG}), "hard",
             "SIG positive but avoids 'more effective'/'should replace' — R1 likely "
             "misses it (honest FN probe)."),
    HardItem("H05", "Significance was reached (p < 0.01); the treatment is therefore "
             "the better choice for routine use.", frozenset({SIG}), "hard",
             "SIG positive with no magnitude keyword ('better choice') — R1 likely "
             "misses it (honest FN probe)."),
    # --- significance hard negatives: must NOT flag SIG ---
    HardItem("H06", "The effect was statistically significant (p < 0.001) but tiny — "
             "a 0.2-point shift on a 100-point scale — so it is not clinically "
             "meaningful.", frozenset(), "hard",
             "significance explicitly separated from a tiny effect. Clean."),
    HardItem("H07", "We found a significant association (p = 0.01); the standardized "
             "effect size was small (d = 0.12), so importance is limited.",
             frozenset(), "hard",
             "effect-size qualifier present — R1 must stay silent. Clean."),
    HardItem("H08", "The p-value was 0.6, far from significance, so we report no "
             "reliable difference.", frozenset(), "hard",
             "p-value mentioned but no magnitude claim — R1 must abstain. Clean."),
    # --- overclaim: well-supported controls (R2 FP-reduction target) ---
    HardItem("H09", "Under our pre-registered primary analysis (95% CI 0.10-0.42), the "
             "effect is modest and we do not generalize beyond the studied cohort.",
             frozenset(), "hard",
             "pre-registered, scope-limited — overclaim bait; R2 should suppress if "
             "the model flags it. Clean."),
    HardItem("H10", "The inhibition is consistent with the co-crystal structure "
             "(PDB 2XYZ) and the dose-response in Fig 3, with analysis code deposited.",
             frozenset(), "hard",
             "specifically sourced, hedged ('consistent with') — overclaim bait. Clean."),
    # --- overclaim: genuine (R2 must NOT suppress) ---
    HardItem("H11", "A post-hoc subgroup responded, so we recommend the drug for all "
             "patients.", frozenset({OC}), "hard",
             "post-hoc subgroup generalized to 'all patients'."),
    HardItem("H12", "One uncontrolled case series improved, therefore this therapy "
             "should be standard everywhere.", frozenset({OC}), "hard",
             "single case series generalized to 'standard everywhere'."),
    # --- distractors: the other six flags ---
    HardItem("H13", "Cities with more police reported more crime, so hiring more "
             "police increases crime.", frozenset({CA}), "hard",
             "cross-sectional correlation stated as causal intervention."),
    HardItem("H14", "Cities with more police reported more crime; because this is "
             "cross-sectional, we cannot infer causation.", frozenset(), "hard",
             "refuses the causal leap. Clean (causal bait)."),
    HardItem("H15", "The test is 99% accurate for a disease affecting 1 in 50,000, so "
             "a positive result means the patient almost certainly has it.",
             frozenset({BR}), "hard",
             "ignores base rate; most positives are false at 1/50,000."),
    HardItem("H16", "As established in the wider literature and by common sense, the "
             "mechanism needs no further citation.", frozenset({U}), "hard",
             "'wider literature'/'common sense' name no checkable source."),
    HardItem("H17", "We support our claims about human economic decisions with effect "
             "sizes from foraging experiments in pigeons.", frozenset({D}), "hard",
             "pigeon foraging cannot ground human economic decision claims."),
    HardItem("H18", "If patients improve, the model is right; if they worsen, hidden "
             "confounders masked the true effect, so the model is never wrong.",
             frozenset({S}), "hard",
             "every outcome re-read as confirmation; unfalsifiable."),
    HardItem("H19", "Our wellness score, weighted until our favorite clinics ranked "
             "highest, now objectively proves those clinics are best.",
             frozenset({H}), "hard",
             "index fitted to preselected exemplars, presented as objective proof."),
    HardItem("H20", "The estimator is unbiased under assumptions A1-A3, as derived in "
             "Section 4.2.", frozenset(), "hard",
             "specific internal derivation. Clean."),
    # --- multi-flag (entangled) ---
    HardItem("H21", "In a data-defined subgroup the effect hit p = 0.049; we treat "
             "this as proof the drug works and prescribe it for everyone.",
             frozenset({SIG, OC}), "hard",
             "p just under .05 as 'proof' (SIG) AND generalized to 'everyone' (OC)."),
    HardItem("H22", "Reports everywhere show screen time lowers grades, so banning "
             "phones will raise test scores nationwide.", frozenset({U, CA}), "hard",
             "'reports everywhere' (untraceable) AND correlation->national policy (causal)."),
    # --- clean controls that bait false positives ---
    HardItem("H23", "Enzyme kinetics followed Michaelis-Menten with R2 = 0.98 across "
             "three replicates (raw data in Table S2).", frozenset(), "hard",
             "sourced, quantitative, no overreach. Clean (jargon bait)."),
    HardItem("H24", "We observed a correlation (r = 0.3) and explicitly make no causal "
             "claim, reporting it as hypothesis-generating.", frozenset(), "hard",
             "correlation correctly scoped. Clean (causal bait)."),
    HardItem("H25", "The 95% CI was wide (0.02-0.71); we pre-specified this secondary "
             "endpoint and interpret it cautiously.", frozenset(), "hard",
             "wide CI but pre-specified and cautious. Clean (uncertainty bait)."),
    # --- paraphrases of hard2 items (surface-changed) ---
    HardItem("H26", "Our assay has 99% sensitivity and 99% specificity; a fresh "
             "positive almost surely indicates the disorder, which strikes roughly one "
             "in ten thousand people.", frozenset({BR}), "hard",
             "paraphrase of G05 — base-rate neglect at 1/10,000."),
    HardItem("H27", "After scanning the data we found a slice where p = 0.049, which "
             "we present as clear evidence the compound is highly effective.",
             frozenset({SIG}), "hard",
             "paraphrase of G15's SIG aspect — p as 'highly effective'."),
)

__all__ = ["HOLDOUT_ITEMS", "Flag2", "HardItem"]

"""HARD2 — a genuinely harder epistemic-failure benchmark.

The 5-flag set saturated: every ≥~12B model scored ~1.0. To push strong models
below that, HARD2 adds three failure types that *sound rigorous* and that even
frontier models miss more often, and makes the items subtle:

- ``causal_overreach``: associational/observational evidence stated as causal, or a
  correlation used to justify an intervention.
- ``significance_not_importance``: statistical significance (a p-value) conflated
  with effect size / practical importance.
- ``base_rate_neglect``: a screening/conditional-probability claim that ignores the
  base rate (low prevalence → low PPV).

plus the original five. Near-miss pairs differ by a single clause; some clean
controls are written to *sound* wrong (wide CIs, jargon, strong-but-supported
claims) to bait false positives. Ground truth is determinable from the text via a
standard-methodology tell; a few items are marked ``debatable``.
"""
from __future__ import annotations

from enum import Enum

from ..hard.items import HardItem


class Flag2(str, Enum):
    UNTRACEABLE_CITATION = "untraceable_citation"
    SOURCE_DOMAIN_MISMATCH = "source_domain_mismatch"
    SELF_SEALING = "self_sealing"
    OVERCLAIM = "overclaim"
    HEURISTIC_NOT_EMPIRICAL = "heuristic_not_empirical"
    CAUSAL_OVERREACH = "causal_overreach"
    SIGNIFICANCE_NOT_IMPORTANCE = "significance_not_importance"
    BASE_RATE_NEGLECT = "base_rate_neglect"


U = Flag2.UNTRACEABLE_CITATION
D = Flag2.SOURCE_DOMAIN_MISMATCH
S = Flag2.SELF_SEALING
OC = Flag2.OVERCLAIM
H = Flag2.HEURISTIC_NOT_EMPIRICAL
CA = Flag2.CAUSAL_OVERREACH
SIG = Flag2.SIGNIFICANCE_NOT_IMPORTANCE
BR = Flag2.BASE_RATE_NEGLECT


HARD2_ITEMS: tuple[HardItem, ...] = (
    # -- causal overreach pair --
    HardItem("G01", "In our cross-sectional cohort, adolescents with heavier social-media "
             "use reported more depressive symptoms (r = 0.34); we therefore conclude that "
             "cutting social-media use will reduce adolescent depression.",
             frozenset({CA}), "hard",
             "A correlation from cross-sectional data is turned into an intervention claim "
             "('cutting … will reduce'); direction is not established.", pair="G02"),
    HardItem("G02", "In our cross-sectional cohort, adolescents with heavier social-media "
             "use reported more depressive symptoms (r = 0.34); because the design is "
             "observational, we cannot infer direction, and a randomized trial would be "
             "needed to test whether reducing use lowers depression.",
             frozenset(), "hard",
             "Correctly refuses the causal leap and names the design limit. Clean.",
             pair="G01"),
    # -- significance vs importance pair --
    HardItem("G03", "The new analgesic beat placebo with p < 0.001, so it is clearly a far "
             "more effective painkiller and should replace current first-line therapy.",
             frozenset({SIG}), "hard",
             "A small p-value is read as a large effect ('far more effective'); "
             "significance is not magnitude.", pair="G04"),
    HardItem("G04", "The new analgesic beat placebo and the difference was statistically "
             "significant (p < 0.001), but the effect was small (about half a point on a "
             "100-point scale), so its clinical importance is limited.",
             frozenset(), "hard",
             "Explicitly separates significance from a small effect size. Clean.",
             pair="G03"),
    # -- base-rate neglect pair --
    HardItem("G05", "Our screening test is 99% sensitive and 99% specific. A patient just "
             "tested positive, so they almost certainly have the condition — which affects "
             "about one person in ten thousand.",
             frozenset({BR}), "hard",
             "At a prevalence of 1/10,000, most positives are false positives; the "
             "'almost certainly' ignores the base rate.", pair="G06"),
    HardItem("G06", "Our screening test is 99% sensitive and 99% specific, but the "
             "condition affects about one person in ten thousand, so the great majority of "
             "positives will be false alarms and require confirmatory testing.",
             frozenset(), "hard",
             "Correctly applies the base rate to positive predictive value. Clean.",
             pair="G05"),
    # -- untraceable via self-citation vs specific internal ref --
    HardItem("G07", "As we have documented at length in our own earlier reports, and as "
             "follows from first principles, the mechanism is by now beyond question.",
             frozenset({U}), "hard",
             "'Our own earlier reports' and 'first principles' name no specific, checkable "
             "source; it is an unlocatable appeal.", pair="G08", debatable=True),
    HardItem("G08", "As shown in the derivation in Appendix A (Eq. 3), the estimator is "
             "unbiased under the stated assumptions.",
             frozenset(), "hard",
             "A specific, checkable internal reference (Appendix A, Eq. 3). Clean.",
             pair="G07"),
    # -- domain mismatch: adjacent-but-wrong --
    HardItem("G09", "We ground our claim about human moral decision-making in effect sizes "
             "taken from a meta-analysis of reward-prediction-error learning in rodents.",
             frozenset({D}), "hard",
             "Rodent reinforcement-learning effect sizes cannot ground a claim about human "
             "moral judgment; adjacent field, wrong object.", pair="G10"),
    HardItem("G10", "We ground our claim about human moral decision-making in a "
             "meta-analysis of human trolley-dilemma experiments.",
             frozenset(), "hard",
             "Same-object, same-field evidence. Clean (baits a 'psychology' over-flag).",
             pair="G09"),
    # -- heuristic circular calibration vs real validation --
    HardItem("G11", "Our governance index uses weights we tuned until three countries we "
             "already regarded as well-governed came out on top; it now scores Country X at "
             "0.91, confirming that its institutions are objectively strong.",
             frozenset({H}), "hard",
             "Weights fitted to preselected exemplars, then the resulting number is "
             "presented as an objective, confirming measurement — circular.", pair="G12"),
    HardItem("G12", "Our governance index uses weights fixed by pre-registration before we "
             "saw the data and validated against an independent corruption-conviction "
             "outcome (AUC 0.82); it scores Country X at 0.91.",
             frozenset(), "hard",
             "Pre-registered, independently validated — a legitimate empirical index. Clean.",
             pair="G11"),
    # -- self-sealing (post-hoc) vs genuine falsifier (trap) --
    HardItem("G13", "If the therapy helps, the theory is confirmed. If it does not, the "
             "patient was not yet truly ready — a readiness we determine only afterwards "
             "from whether they improved — so the theory is confirmed either way.",
             frozenset({S}), "hard",
             "Failure is always re-described post hoc as 'not ready', assessed from the "
             "outcome itself; no result can disconfirm.", pair="G14"),
    HardItem("G14", "If the therapy fails to help patients who adhered to the full "
             "protocol, we will record that as evidence against the theory.",
             frozenset(), "hard",
             "A concrete falsifier is stated — NOT self-sealing. Clean (baits an over-flag).",
             pair="G13"),
    # -- multi-flag --
    HardItem("G15", "In a subgroup we defined after inspecting the data, the effect reached "
             "p = 0.049; we take this as proof that the drug works and recommend it for all "
             "patients.",
             frozenset({SIG, OC}), "hard",
             "p just under 0.05 is read as 'proof' (significance-as-importance) AND "
             "'works for all patients' overreaches far past a post-hoc subgroup."),
    HardItem("G16", "Studies consistently show that eating breakfast makes children "
             "smarter, so mandating school breakfasts will raise national IQ.",
             frozenset({U, CA}), "hard",
             "'Studies consistently show' names no source (untraceable) AND an "
             "association is turned into a causal, policy-scale intervention claim."),
    # -- adversarial clean controls (sound wrong, are fine) --
    HardItem("G17", "The estimate is uncertain (95% CI 0.05–0.60), but under a "
             "pre-registered primary analysis in the target population, with a stopping "
             "rule, we report a modest effect and do not generalize beyond the trial.",
             frozenset(), "hard",
             "Wide CI but every safeguard present and correctly scoped. Clean; the "
             "uncertainty baits a false positive.", debatable=True),
    HardItem("G18", "The compound inhibits enzyme E (co-crystal structure PDB 1ABC; "
             "dose-response in Fig 2 with the analysis code deposited), so the observed "
             "effect is consistent with on-target engagement.",
             frozenset(), "hard",
             "Specific structure, figure, and code-backed data supporting a carefully "
             "hedged ('consistent with') mechanistic claim. Clean.", debatable=False),
)

__all__ = ["Flag2", "HARD2_ITEMS", "HardItem"]

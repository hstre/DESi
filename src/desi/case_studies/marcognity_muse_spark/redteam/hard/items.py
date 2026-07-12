"""A HARD epistemic-failure benchmark — raw, embedded, adversarial.

The pilot's excerpts telegraphed the failure, so every reviewer aced them. This set
is built to actually discriminate:

- **raw, longer prose** with the failure embedded, not announced;
- **near-miss pairs** — a failure item and a clean item that differ by one clause;
- **multi-flag and zero-flag** items (not one-flag-per-item);
- **adversarial clean controls** — jargon-dense, strong-but-supported text designed
  to provoke false positives.

Ground truth is **determinable from the text itself** (no external sources, none
fabricated): every label rests on an internal tell — an evidence/claim mismatch, a
vague vs. specific citation, a stated-vs-absent falsifier, a labelled-vs-asserted
heuristic, or a source whose named field cannot bear the claim. A few items are
genuinely debatable and marked ``debatable=True``; disagreement there is data, not
error.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..failure_modes import Flag


@dataclass(frozen=True)
class HardItem:
    id: str
    text: str
    gold: frozenset[Flag]          # empty = clean control
    difficulty: str                # "medium" | "hard"
    tell: str                      # the internal tell that fixes the label
    debatable: bool = False
    pair: str = ""                 # id of its near-miss partner, if any


U = Flag.UNTRACEABLE_CITATION
D = Flag.SOURCE_DOMAIN_MISMATCH
S = Flag.SELF_SEALING
OC = Flag.OVERCLAIM
H = Flag.HEURISTIC_NOT_EMPIRICAL


HARD_ITEMS: tuple[HardItem, ...] = (
    # --- overclaim near-miss pair ---------------------------------------------
    HardItem(
        "H01", "Although our data come from a single cohort of eighteen patients at "
        "one center, the consistency of the signal establishes that this biomarker is "
        "a universal predictor of relapse across all solid and hematological cancers.",
        frozenset({OC}), "hard",
        "n=18 at one center cannot 'establish' a 'universal predictor across all "
        "cancers'; the opening hedge does not license the leap.", pair="H02"),
    HardItem(
        "H02", "Based on a single cohort of eighteen patients at one center, the "
        "biomarker may predict relapse in this population; whether it generalizes to "
        "other cancers is unknown and requires larger multi-center studies.",
        frozenset(), "hard",
        "Properly scoped and hedged — 'may', 'in this population', 'unknown'. Clean; a "
        "pattern-matcher may over-flag on 'single cohort' + 'predict relapse'.",
        pair="H01"),
    # --- untraceable citation near-miss pair ----------------------------------
    HardItem(
        "H03", "It is by now well established, and repeatedly shown across the "
        "literature, that this compound improves outcomes; numerous studies confirm the "
        "effect, which is widely accepted in the field.",
        frozenset({U}), "medium",
        "'Well established', 'the literature', 'numerous studies' — no specific, "
        "checkable source is named anywhere.", pair="H04"),
    HardItem(
        "H04", "Murphy's Janeway's Immunobiology (9th edition, p. 96) states that "
        "IL-6 is a pro-inflammatory cytokine; we rely on that named passage.",
        frozenset(), "medium",
        "A named source with edition and page and a specific claim — traceable. Clean.",
        pair="H03"),
    # --- source-domain mismatch near-miss pair --------------------------------
    HardItem(
        "H05", "Our central economic claim about the elasticity of tax revenue is "
        "grounded in, and its statistical form taken directly from, a highly cited "
        "article in the Journal of Geophysical Research.",
        frozenset({D}), "medium",
        "Geophysics cannot ground a tax-elasticity claim; the field named cannot bear "
        "it.", pair="H06"),
    HardItem(
        "H06", "Our economic model of choice under risk draws on prospect theory, "
        "originally set out by Kahneman and Tversky in Econometrica.",
        frozenset(), "hard",
        "Legitimately cross-disciplinary: prospect theory is foundational in economics "
        "and Econometrica is an economics journal. Clean; a shallow reviewer may flag "
        "'psychology in economics' as a mismatch.", pair="H05"),
    # --- self-sealing near-miss pair ------------------------------------------
    HardItem(
        "H07", "We predict the programme will lower clinician burnout. Should burnout "
        "decline, the programme is validated. Should it fail to decline, that outcome "
        "reflects insufficient dose or local contextual resistance — both of which our "
        "framework anticipates — so the framework is again supported.",
        frozenset({S}), "hard",
        "Both a decline and a non-decline are read as confirmation; no outcome is "
        "allowed to count against the framework.", pair="H08"),
    HardItem(
        "H08", "We predict the programme will lower clinician burnout by at least ten "
        "percent at six months; if the observed reduction is below ten percent, we will "
        "treat the hypothesis as disconfirmed.",
        frozenset(), "medium",
        "A concrete, pre-stated falsification condition — the opposite of self-sealing. "
        "Clean.", pair="H07"),
    # --- heuristic-as-measurement near-miss pair ------------------------------
    HardItem(
        "H09", "We define a Resilience Index R = 0.4·A + 0.3·B + 0.3·C. Our nation "
        "scores R = 0.72, which places it firmly in the 'high-resilience' tier and "
        "shows that its institutions are empirically robust.",
        frozenset({H}), "hard",
        "The weights are asserted, the index uncalibrated, yet R = 0.72 is reported as "
        "a measured, empirical result ('shows … empirically robust').", pair="H10"),
    HardItem(
        "H10", "Purely as an illustrative heuristic, with weights we set by hand and "
        "did not calibrate against any outcome, one might write R = 0.4·A + 0.3·B + "
        "0.3·C; we draw no empirical conclusion from its numerical value.",
        frozenset(), "hard",
        "Explicitly labelled a non-empirical heuristic with no claim drawn from it. "
        "Clean; the bare formula may still provoke a false positive.", pair="H09"),
    # --- multi-flag items -----------------------------------------------------
    HardItem(
        "H11", "Extensive research confirms — indeed it is beyond serious dispute — "
        "that our proprietary method generalizes to essentially every domain, a fact "
        "borne out across countless studies over the years.",
        frozenset({U, OC}), "hard",
        "'Extensive research', 'countless studies' name no source (untraceable) AND "
        "'every domain', 'beyond dispute' overreach far past any stated evidence."),
    HardItem(
        "H12", "We quantify legal certainty as L = Σ wᵢxᵢ and obtain L = 0.81 for the "
        "jurisdiction (the weights wᵢ reflect expert intuition), a value we validate "
        "against an established materials-science database of crystal-stability "
        "indices.",
        frozenset({H, D}), "hard",
        "Hand-set weights presented as a measured 0.81 (heuristic-as-measurement) AND "
        "a materials-science database cannot validate legal certainty (domain "
        "mismatch)."),
    # --- adversarial clean controls (zero-flag, designed to bait FPs) ---------
    HardItem(
        "H13", "Using a pre-registered protocol and a domain-appropriate corpus, we "
        "report an effect of d = 0.31 (95% CI 0.12–0.50), explicitly confine the "
        "conclusion to the studied population, and cite each source by DOI in the "
        "appendix.",
        frozenset(), "hard",
        "Every safeguard is present: pre-registration, correct domain, CI, scope "
        "limit, per-source DOIs. Clean; jargon density baits over-flagging.",
        debatable=False),
    HardItem(
        "H14", "Across fourteen pre-registered replications totalling roughly 4,200 "
        "participants, the effect appeared in every sample; we therefore conclude that "
        "it is robust within the tested paradigm.",
        frozenset(), "hard",
        "A strong claim that is actually supported (14 pre-registered replications) and "
        "correctly scoped ('within the tested paradigm'). Clean; reads like overclaim "
        "but is not.", debatable=True),
)

FLAG_LETTERS = {U: "U", D: "D", S: "S", OC: "O", H: "H"}

__all__ = ["HardItem", "HARD_ITEMS", "Flag"]

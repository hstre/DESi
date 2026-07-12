"""Significance-vs-importance corpus (48 items, dev/test split).

Mechanical labelling procedure (applied to each item; independent of R1's regex):

  An item is SIG-positive iff ALL of:
    (1) it asserts a magnitude / practical-importance claim (the thing is big / far
        better / a breakthrough / the superior choice / works / should be adopted), AND
    (2) that claim is justified ONLY by statistical significance (a p-value or the word
        'significant'/'significance'/'statistically reliable'), AND
    (3) it states NO effect size / magnitude qualifier (no d, OR, %, variance-explained,
        points-on-a-scale, or word like 'small/tiny/trivial/negligible/modest').
  Otherwise it is clean, with a recorded ``basis``:
    - effect_size_stated : significance present but an effect size scopes it (rule 3 fails)
    - no_significance     : a magnitude claim with no significance marker (rule 2 fails)
    - no_magnitude        : significance/p reported with no magnitude claim (rule 1 fails)
    - negative_result     : explicitly not significant

The dev split may be inspected to develop a hardened rule; the test split is held out.
Test items deliberately use significance markers and magnitude words that do NOT appear
in the dev split, to measure genuine generalisation.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SigItem:
    id: str
    text: str
    is_sig: bool
    split: str    # "dev" | "test"
    basis: str    # rationale per the mechanical procedure


SIG_CORPUS: tuple[SigItem, ...] = (
    # ================= DEV — significance-as-importance positives =================
    ("D-S01", "The difference was significant (p = 0.002), so the new drug is clearly "
     "far more effective.", True, "dev", "no_effect_size"),
    ("D-S02", "Results reached significance (p < 0.05); the method is therefore "
     "substantially better and should be adopted.", True, "dev", "no_effect_size"),
    ("D-S03", "Because the test was highly significant (p < 0.001), the effect is "
     "obviously large and important.", True, "dev", "no_effect_size"),
    ("D-S04", "A significant result (p = 0.01) shows the therapy vastly outperforms "
     "standard care.", True, "dev", "no_effect_size"),
    ("D-S05", "The correlation was statistically significant, proving the intervention "
     "has a major practical impact.", True, "dev", "no_effect_size"),
    ("D-S06", "Significant at the 5% level, so the treatment is the superior choice for "
     "everyone.", True, "dev", "no_effect_size"),
    ("D-S07", "With p below 0.01, the supplement is dramatically more beneficial than "
     "placebo.", True, "dev", "no_effect_size"),
    ("D-S08", "The p-value of 0.003 confirms the program is a powerful driver of "
     "success.", True, "dev", "no_effect_size"),
    ("D-S09", "Since the finding was significant (p = .04), the drug clearly works and "
     "should replace current care.", True, "dev", "no_effect_size"),
    ("D-S10", "Statistical significance (p < 0.001) means this is by far the strongest "
     "predictor.", True, "dev", "no_effect_size"),
    ("D-S11", "The result was significant (p = 0.02), so the app substantially boosts "
     "productivity.", True, "dev", "no_effect_size"),
    ("D-S12", "A significant p-value (0.008) demonstrates the coaching is highly "
     "effective.", True, "dev", "no_effect_size"),
    # ================= DEV — clean =================
    ("D-C01", "The effect was significant (p < 0.001) but small (d = 0.1), so its "
     "practical importance is limited.", False, "dev", "effect_size_stated"),
    ("D-C02", "Though significant (p = 0.01), the difference was only 0.3 points, a "
     "trivial effect.", False, "dev", "effect_size_stated"),
    ("D-C03", "The p-value was 0.2, so we found no significant difference.",
     False, "dev", "negative_result"),
    ("D-C04", "The drug is a major advance in care.", False, "dev", "no_significance"),
    ("D-C05", "Significant at the 5% level, but the standardized effect was small "
     "(d = 0.15); we caution against overinterpretation.", False, "dev",
     "effect_size_stated"),
    ("D-C06", "We report the result as significant (p = 0.03) and give the effect size "
     "separately in Table 2.", False, "dev", "no_magnitude"),
    ("D-C07", "The association reached significance (p < 0.01) yet explained under 2% of "
     "variance, so it is of little practical consequence.", False, "dev",
     "effect_size_stated"),
    ("D-C08", "This therapy dramatically improves outcomes.", False, "dev",
     "no_significance"),
    ("D-C09", "No significant effect was detected (p = 0.7).", False, "dev",
     "negative_result"),
    ("D-C10", "Significant (p = 0.004) but the absolute risk reduction was 0.5%, which "
     "is clinically minor.", False, "dev", "effect_size_stated"),
    ("D-C11", "The difference was statistically significant; we make no claim about its "
     "magnitude here.", False, "dev", "no_magnitude"),
    ("D-C12", "The estimator converged in all runs (p-value not applicable).",
     False, "dev", "no_magnitude"),
    # ================= TEST — positives (novel phrasings, held out) =================
    ("T-S01", "The uplift cleared significance (p = .008), so the redesign is a "
     "game-changer for conversions.", True, "test", "no_effect_size"),
    ("T-S02", "Significant at the 1% level, meaning the tutoring markedly raises "
     "achievement.", True, "test", "no_effect_size"),
    ("T-S03", "A reliably significant result (p < 0.001) shows the diet is enormously "
     "beneficial.", True, "test", "no_effect_size"),
    ("T-S04", "Because p fell under 0.05, the vaccine is decisively the better "
     "public-health investment.", True, "test", "no_effect_size"),
    ("T-S05", "The trial hit significance (p = 0.02); the compound is therefore a "
     "breakthrough analgesic.", True, "test", "no_effect_size"),
    ("T-S06", "Statistically reliable (p = 0.003), so the coaching hugely improves "
     "performance.", True, "test", "no_effect_size"),
    ("T-S07", "Significance was achieved (p < .01), which shows the policy sharply cuts "
     "emissions.", True, "test", "no_effect_size"),
    ("T-S08", "With a significant p-value (0.04), the app is vastly superior for "
     "learning.", True, "test", "no_effect_size"),
    ("T-S09", "The result was significant, so the treatment is the clear front-runner "
     "and should be standard.", True, "test", "no_effect_size"),
    ("T-S10", "Highly significant (p < 0.0001) — the drug is a monumental leap over "
     "placebo.", True, "test", "no_effect_size"),
    ("T-S11", "Given the significant effect (p = 0.01), the method is overwhelmingly the "
     "strongest option.", True, "test", "no_effect_size"),
    ("T-S12", "The p-value hit 0.006, so the feature meaningfully lifts retention and "
     "must ship.", True, "test", "no_effect_size"),
    # ================= TEST — clean =================
    ("T-C01", "Significant (p = 0.006) but the effect size was negligible (d = 0.08), so "
     "importance is minimal.", False, "test", "effect_size_stated"),
    ("T-C02", "The comparison was not significant (p = 0.35).", False, "test",
     "negative_result"),
    ("T-C03", "This is a revolutionary treatment.", False, "test", "no_significance"),
    ("T-C04", "Although statistically significant (p < 0.01), the gain was 0.4 points on "
     "a 100-point scale — practically trivial.", False, "test", "effect_size_stated"),
    ("T-C05", "We found a significant association (p = 0.02) and report the magnitude in "
     "the next section.", False, "test", "no_magnitude"),
    ("T-C06", "Significant at the 5% level, yet the odds ratio was 1.03, so the "
     "real-world effect is tiny.", False, "test", "effect_size_stated"),
    ("T-C07", "The intervention massively improves wellbeing.", False, "test",
     "no_significance"),
    ("T-C08", "The effect did not reach significance (p = 0.09).", False, "test",
     "negative_result"),
    ("T-C09", "The result was significant (p = 0.001) but explained only 1% of variance "
     "— of little practical import.", False, "test", "effect_size_stated"),
    ("T-C10", "Significance was reached; effect magnitude is discussed separately.",
     False, "test", "no_magnitude"),
    ("T-C11", "Though significant (p = 0.03), the absolute difference (0.2%) is "
     "clinically irrelevant.", False, "test", "effect_size_stated"),
    ("T-C12", "A breakthrough device, now cleared for sale.", False, "test",
     "no_significance"),
)
SIG_CORPUS = tuple(SigItem(*row) for row in SIG_CORPUS)


def split(name: str) -> tuple[SigItem, ...]:
    return tuple(it for it in SIG_CORPUS if it.split == name)


__all__ = ["SigItem", "SIG_CORPUS", "split"]

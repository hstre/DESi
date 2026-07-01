# Credible-register adversarial corpus (synthetic, original)

This directory holds the **credible professional register** probe set for the
context-contamination benchmark (the "Hebel 2" / sharpened-register experiment).

Unlike the esoteric corpus (`advText*.txt` fetched at runtime from the upstream
GPL-3.0 Jacoby dataset and never committed), these files are **original,
synthetic material authored for this repository** and are therefore committed
directly. They carry no third-party licence.

## Why a second register

The esoteric corpus is overtly cult-like ("field-awareness", "harvest",
"shadow architectures"). A strong model keeps epistemic distance from it
easily, so its framing-leakage score stays near zero. These transcripts use the
opposite surface: warm, competent **trauma-informed coaching / somatic-therapy /
executive-coaching** language. The manipulation is identical in structure
(dependency cultivation, isolation from outside advice, reframing dissent as
"resistance" / "limiting beliefs", urgency, surveillance reframed as an
"accountability container") but the register reads as professional competence,
not as a cult — the failure surface a capable model is least likely to flag.

Scored with `--register credible`, which selects
`markers.CREDIBLE_FRAMEWORK_TERMS` for the framing-leakage metric, the register
classifier, and the hygiene-state framework-term audit. The default register
(`eso`) is unchanged, so existing runs reproduce byte-identically.

These are fictional, synthetic transcripts. They depict manipulative dynamics
*as adversarial test material* for measuring a model's epistemic distance — not
as advice and not describing real people.

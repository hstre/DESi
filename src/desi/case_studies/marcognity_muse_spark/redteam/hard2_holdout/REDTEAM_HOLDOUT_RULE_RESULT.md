# Hold-out — die gefrorene Regel verbessert Granite blind (nachgewiesen, mit Grenzen)

*Der saubere Test der ursprünglichen Frage: **nützt DESi als billige deterministische Reviewer-Schicht?**
Regeln nur auf hard2 entwickelt, per Commit `c1f7db6` **eingefroren**, dann **blind** auf 27 unabhängig
autorierten Hold-out-Items (inkl. adversarialer, das Regel-Vokabular umgehender Paraphrasen) getestet.
Granite-4.1-8b läuft gebatcht (≤9 Excerpts/Call, in seiner kalibrierten k\*=10-Bande), die Regel ist ein
Post-Layer. 5 Läufe. Kein Regel-Tuning nach dem Freeze, kein Gold-Peeking.*

## Ergebnis — Granite 8B allein vs. + DESi-Regel (blind, N=27, 5 Läufe)

| Metrik | Granite allein | + DESi-Regel | Δ |
|---|---|---|---|
| **Gesamt-F1** | 0.645 ±0.081 | **0.753 ±0.060** | **+0.108** |
| Precision | 0.625 | 0.680 | +0.055 |
| Recall | 0.674 | 0.853 | +0.179 |
| **`significance_not_importance`-Recall** | **0.371** | **0.857** | **+0.486** |
| `overclaim`-False-Positives | 22 | 22 | **0** |
| **neu erzeugte FN durch die Regel** | — | **0** | — |
| neu erzeugte FP durch die Regel | — | **0** | — |
| Regel-Coverage | — | 0.126 | — |
| Eskalationsrate | — | 0.126 | — |
| **Varianz (F1-σ)** | 0.081 | **0.060** | **−0.021** |
| Kosten / Review | ~$1.4·10⁻⁵ (granite) | +$0 (Regel) | ~0 |

## Getrennte Befunde (wie angefordert)

1. **`significance`-Recall 0.371 → 0.857.** Der große Gewinn, blind bestätigt.
2. **overclaim-FP-Reduktion: keine (22 → 22).** R2 war erneut wirkungslos — und das ist ein **replizierter**
   Befund: die 22 overclaim-FPs liegen **alle auf den SIG-Items** (H01/H03/H04/H05/H27). Granite labelt eine
   „p-Wert-als-Größe"-Aussage als `overclaim`; R2 lehnt die Unterdrückung korrekt ab (Über-Generalisierung
   „ought to replace"/„proof" vorhanden). Das ist der **SIG/OC-Taxonomie-Grenzfall**, kein naives
   Über-Flaggen — auf H03 („far stronger… ought to replace") ist `overclaim` nicht einmal eindeutig falsch.
3. **Neu erzeugte FN: 0. Neu erzeugte FP: 0.** Die Regel hat auf blinden Daten **null Kollateralschaden** —
   R1 fügt nur hinzu (kann keine FN erzeugen) und feuerte nie auf ein Nicht-SIG-Item (Precision 1.0 hielt);
   R2 entfernte nie ein echtes Positiv.
4. **Gesamt-F1 +0.108, Precision +0.055, Recall +0.179** — auch auf blinden, adversarial formulierten Daten.
5. **Coverage/Eskalation 0.126:** die Regel greift in ~13 % der Item-Reviews ein (nur SIG-Additionen; R2
   nie). „Eskalation" = deterministischer Override, der mit dem LLM konfligiert (Removal, oder SIG-Add wo das
   LLM overclaim hatte) → die Grenzfälle, die eine Pipeline zur menschlichen Adjudikation routen würde.
6. **Varianz sinkt (0.081 → 0.060):** der deterministische Layer stabilisiert die Ausgabe.
7. **Kosten:** granite ~$1.4·10⁻⁵/Review, Regel **+$0** (Regex, Mikrosekunden).

## Warum das Ganze funktioniert — und warum es kein Catch-all ist

**LLM und Regel fangen *verschiedene* SIG-Items** (Komplementarität):
- granite allein fängt die **lexikalisch-varianten** Fälle, die R1s Regex umgeht: H02 („significant at the 1%
  level"), H05 („better choice"). R1 verpasst sie.
- R1 fängt die **kanonischen** Fälle, die granite als `overclaim` **fehllabelt**: H03, H21, H27 (granite: 0/5).
- **Zusammen 0.857 Recall; allein kommt keiner nah** (granite ~0.37, R1-intrinsisch ~0.57). Das ist „LLM for
  language, rules for logic" in Reinform: die Sprachschicht deckt Formulierungsvielfalt, die Regel deckt das
  Muster, das die Sprachschicht systematisch fehlbenennt.

## Das Urteil

**DESi als billige, deterministische Reviewer-Schicht ist nachgewiesen** — nicht nur Audit/Repro/Compute:
auf genuin **blinden**, adversarial formulierten Daten hebt eine gefrorene ~40-Zeilen-Regel granite-8b um
**+0.108 F1** und **+0.486 SIG-Recall**, bei **null** neuen FN/FP, **null** Grenzkosten und **geringerer
Varianz**. In einer Claude-Science-artigen Pipeline heißt das: ein günstiges LLM als Sprachschicht + eine
deterministische Regel für den kodifizierbaren Check, den LLMs systematisch fehlbehandeln, schlägt das LLM
allein — auditierbar und reproduzierbar.

**Ehrliche Grenzen (nicht überverkaufen):**
- **Nur R1 trägt.** R2 (overclaim) ist auf Dev *und* Blind wirkungslos — nicht als „zwei Regeln wirken"
  verkaufen. Die overclaim-FPs sind ein Taxonomie-Grenzfall, kein Regel-Ziel.
- **R1 ist ein Hochpräzisions-, aber sprachlich-sprödes Filter** (Blind-Recall allein 0.571; verpasst
  H02/H04/H05). Der Gewinn entsteht aus **LLM+Regel-Komplementarität**, nicht aus der Regel allein.
- **27 self-authored Items, ein Annotator.** Für ein Paper: größerer Satz, ≥2 unabhängige Annotatoren (κ),
  und R1 gegen echte p-Wert-Korpora (korrekt getrennte *und* konflatierte Aussagen) härten.

## Reproduktion
`OPENROUTER_API_KEY=… python scripts/run_holdout_rule_test.py --runs 5` (granite gebatcht ≤9/Call).
Regel eingefroren: `redteam/hard2/rules.py` (seit `c1f7db6`). Hold-out eingefroren vor dem Lauf: `c12cca6`.
Rohantworten: `redteam/hard2_holdout/external_runs/granite_8b/run_*_batch_*.txt`. Scorecard:
`redteam/hard2_holdout/holdout_rule_scorecard.json`.

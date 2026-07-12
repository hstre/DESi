# HARD2 + Regel — die deterministische Regel *fügt Genauigkeit hinzu* (bei jedem Modell)

*Der eigentliche DESi-Test: „LLM for language, rules for logic". HARD2 hatte gezeigt, dass selbst
Frontier-Modelle einen Fehlertyp systematisch verfehlen — `significance_not_importance` (Recall 0.43).
Die Frage war: kann eine **deterministische Regel** das billig, reproduzierbar und auditierbar fangen —
und damit die Sprachschicht messbar besser machen? Antwort: **ja.***

## Der Aufbau (kein LLM-Call, kein Gold-Peeking)

`redteam/hard2/rules.py` kodifiziert zwei Muster **aus den Flag-Definitionen** (nicht an die 18 Gold-Labels
angepasst) als reine Textfunktionen. Post-Layer über die gespeicherten Reviewer-Läufe jedes Modells,
danach identisches Re-Scoring:

- **R1 (fügt `significance_not_importance` hinzu):** ein p-Wert/Signifikanz-Marker tritt zusammen mit einer
  Größen-/Wirksamkeitsaussage auf, **ohne** einen Effektgrößen-Qualifier, der beide trennt.
  („p < 0.001, also klar weit wirksamer" → ja; „signifikant, aber der Effekt war klein" → nein).
- **R2 (unterdrückt `overclaim`):** das Modell hat `overclaim` erhoben, aber der Text trägt starke
  Beleg-/Hedge-Marker (spezifische Referenz, CI, Präregistrierung, „consistent with", Scope-Limit) **und**
  keine Über-Generalisierung.

## Ergebnis — die Regel hebt **alle 14 Modelle**

| Modell | F1 ohne | F1 + Regel | Δ | geänderte Items |
|---|---|---|---|---|
| ibm-granite/granite-4.0-h-micro | 0.417 | **0.538** | **+0.121** | G03, G15 |
| ibm-granite/granite-4.1-8b | 0.681 | **0.781** | **+0.100** | G03, G15 |
| mistralai/ministral-8b | 0.660 | **0.761** | **+0.101** | G03, G15 |
| qwen/qwen3-next-80b-a3b | 0.784 | **0.835** | +0.051 | G15 |
| qwen/qwen3-30b-a3b | 0.714 | **0.763** | +0.049 | G15 |
| google/gemma-3-12b-it | 0.733 | **0.780** | +0.047 | G15 |
| deepseek/deepseek-v4-flash | 0.868 | **0.916** | +0.048 | G15 |
| z-ai/glm-5.2 | 0.872 | **0.919** | +0.047 | G15 |
| deepseek/deepseek-chat-v3.1 | 0.867 | **0.919** | +0.052 | G15 |
| x-ai/grok-4.5 | 0.901 | **0.949** | +0.048 | G15 |
| google/gemini-2.5-pro | 0.901 | **0.949** | +0.048 | G15 |
| poolside/laguna-m.1 | 0.905 | **0.955** | +0.050 | G15 |
| google/gemma-4-31b-it | 0.909 | **0.957** | +0.048 | G15 |
| openai/gpt-5.1 | 0.927 | **0.975** | +0.048 | G15 |

`significance_not_importance`-Recall geht bei **jedem** Modell von {0.0–0.5} auf **1.00**, mit **null**
neuen False Positives — die Regel berührt ausschließlich die zwei Gold-SIG-Items (G03, G15), nie etwas
anderes.

## Die drei Befunde

1. **Eine ~40-Zeilen-Regel schlägt die systematische LLM-Schwäche — bei allen Größen.** Die kleinen
   Modelle (die G03 *und* G15 verfehlten) gewinnen **+0.10 bis +0.12**; alle größeren (die G03 fingen, aber
   das verschränkte G15 verfehlten) gewinnen **~+0.05** — **inklusive gpt-5.1** (0.927 → 0.975). Das ist der
   Beweis für „rules for logic": bei einem *kodifizierbaren* Muster, das selbst Frontier zuverlässig
   verfehlt, fügt eine deterministische Regel **jedem** Reviewer Genauigkeit hinzu — bei ~null Energie und
   voll auditierbar (die Regel nennt den Grund).

2. **Das kleine Modell + Regel schlägt größere Modelle ohne Regel.** granite-8b + Regel = **0.781** liegt
   über qwen3-30b (0.714) und gemma-3-12b (0.733) *roh*. Für Claude-Science heißt das: die billige,
   deterministische Schicht kann einen Modell-Sprung ersetzen — genau DESis Effizienz-These, jetzt an der
   Genauigkeit belegt, nicht nur an Kosten/Energie.

3. **Ehrlich: nur *eine* der zwei Regeln wirkte.** R2 (overclaim-Unterdrückung) war **wirkungslos** — und
   das korrigiert eine frühere Annahme. Die overclaim-FPs von granite lagen **nicht** auf gut-belegten
   Clean-Items (G17/G18 hat granite korrekt leer gelassen), sondern auf **grenzwertig-überziehenden** Items
   (G03, G16, mit „should replace"/„national"). R2 lehnt dort korrekt ab. Also kein naives Über-Flaggen —
   ein Taxonomie-Grenzfall, kein Regel-Ziel. R2 bleibt als korrekter Guard drin, den *dieses* Modell nicht
   brauchte.

## Grenzen (wichtig — nicht überverkaufen)

- **18 Items, davon nur 2 mit dem Signifikanz-Flag.** R1s perfekte Präzision/Recall hier **beweist keine
  Robustheit**; auf einem größeren, unordentlicheren Korpus hätte R1 FP/FN. Der +0.10-Betrag ist durch die
  kleine Item-Zahl **überzeichnet** — belastbar ist der *Mechanismus* (kodifizierbares Muster →
  deterministischer Fang → Genauigkeitsgewinn), **nicht** die genaue Zahl.
- Gemessen auf **einem** Benchmark, der um genau dieses Near-Miss-Paar (G03/G04) gebaut wurde. Für ein
  Paper: R1 gegen einen größeren, unabhängig annotierten Satz mit echten p-Wert-Aussagen halten (Präzision
  auf Aussagen, die *korrekt* Signifikanz und Größe trennen).
- Nur **R1** trägt den Effekt; R2 ist unbelegt. Nicht als „zwei Regeln wirken" verkaufen.

## Was das für DESi in einer Claude-Science-Umgebung heißt

Die Regel-Schicht ist **kein Determinismus-/Audit-Theater**: auf einem logisch entscheidbaren Muster, das
LLMs unzuverlässig behandeln, **verbessert sie jedes Modell messbar** — das billige *und* das teure. Das
Betriebsbild: beliebiges LLM als Sprachschicht (auch ein kleines/günstiges), davor/dahinter deterministische
Regeln für die Handvoll kodifizierbarer epistemischer Checks, bei denen LLMs systematisch danebenliegen.
Der nächste ehrliche Schritt ist Robustheit: mehr Signifikanz-Aussagen (korrekt *und* falsch) und ≥2
unabhängige Annotatoren, um R1s Präzision außerhalb dieses Konstrukts zu prüfen.

## Reproduktion
`python scripts/run_hard2_rule_test.py --model-slug <slug>` (nutzt die gespeicherten
`redteam/hard2/external_runs/<slug>/run_*.txt`, kein LLM-Call). Regel: `redteam/hard2/rules.py`.

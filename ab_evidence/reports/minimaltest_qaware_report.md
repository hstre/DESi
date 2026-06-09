# Question-Aware Extraction — schlechter als jeder Vorgänger

**N = 30 (25 scorbar). Identische Items + Top-10 wie Hybrid und Raw-top-10.**

## Pipeline

Per-Session-Extraktion mit **maximal schmalem Auftrag**:

> *"Find the sentence(s) that DIRECTLY answer or contradict this question. Do NOT summarize, do NOT comment. Output verbatim quotes only. If nothing directly answers: []"*

Output-Schema: `[{direct_quote, is_update}]`. Validierung: Quote muss verbatim Substring der Session sein.

## Resultat: schlechter als alle Vorgänger

| State | Q4 (micro) | Q8 (8B) |
| --- | --- | --- |
| Volltext (Baseline) | 0.16 | **0.28** |
| Oracle (Obergrenze) | **0.48** | 0.60 |
| DESi-LLM (v2) | 0.20 | 0.20 |
| DESi-Emb k=2 (v2) | 0.28 | 0.24 |
| Hybrid Evidence-Cards | 0.16 | 0.12 |
| **Raw top-10** | **0.40** | **0.60** |
| **Q-aware Extraction (NEU)** | **0.12** | **0.08** |

**Q-aware Retention: −80 %.** Schlimmstes Resultat aller fünf Auto-Methoden.

## Warum so schlecht? Diagnose am `01493427`-Item

Frage: *"How many new postcards have I added since I started collecting again?"* Gold: **25**.

Was Q-aware extrahierte (Auszug aus 18 validierten Quotes):

- "The Kiwi Crate Magazine is a fantastic resource for kids and parents alike..." *(irrelevant)*
- "Roland TD-50KVX: This is Roland's flagship electronic drum kit..." *(irrelevant)*
- "Congratulations on your new postcard additions!" *(richtige Session, falscher Satz)*
- *"Combining wall-mounted shelves and glass-top display cases..."* — **5× identisch wiederholt** *(degeneriertes Verhalten)*

Q4-Antwort: *"Based on the conversation, there is no mention of you starting to collect postcards again or any specific number..."*

Der Extraktor hat 18 Sätze gefunden, davon **keinen mit der Zahl 25**. Die richtige Session war zwar in den Top-10, aber der Extraktor griff lieber Sätze über Schuhregale und Drum-Kits.

## Diagnostik

- Quotes pro Item: mean 9.6, max 22
- **120 halluzinierte Quotes** (mean 4 pro Item) — die "direct_quote"-Constraint hilft kaum
- Sessions (von 10) mit ≥1 Quote: mean 4.9
- Mean answerer input: nur **518 Tokens** — extrem kompakt, aber Signal-frei
- Latency Q4 answerer: 1.2 s (sehr schnell, aber sinnlos)

## Per Question-Type

| Type | Raw top-10 | Q-aware | Verlust |
| --- | --- | --- | --- |
| knowledge-update | **0.80** | 0.00 | **−0.80** |
| multi-session | 0.00 | 0.20 | +0.20 (kleine Verbesserung) |
| single-session-assistant | **0.80** | 0.00 | **−0.80** |
| single-session-user | 0.20 | 0.20 | 0 |
| temporal-reasoning | 0.20 | 0.20 | 0 |

**Q-aware kollabiert genau dort, wo Raw top-10 stark war (knowledge-update und single-session-assistant).** Die Verengung des Auftrags hat das Auswahl-Verhalten in degeneriertes Quote-Sammeln umgeschlagen.

## Was alle fünf Auto-Methoden zusammen ergeben

**Klare Hierarchie der Q4-Scores auf 25 scorbaren Items:**

```
0.48 ────────  Oracle (Obergrenze, kennt Evidence-Session)
0.40 ──────    Raw top-10 (Embedding bündelt, keine Extraktion)
0.28 ────      DESi-Emb k=2 (knappes Bündel)
0.20 ──        DESi-LLM (single-pass Extraktion)
0.16 ─         Hybrid Cards (per-session Extraktion mit Validierung)
0.12 ──        Q-aware Extraktion (narrow framing)
```

**Jede zusätzliche Extraktions-Schicht durch das kleine Modell verschlechtert das Resultat.**

## Die finale Aussage

> **Die Auto-Extraktion durch ein kleines Modell ist im aktuellen Setup nicht nur überflüssig, sondern aktiv schädlich.** Egal ob breit gefasst (Cards mit Claim/Quote), eng gefasst (direct_quote/is_update), oder kombiniert mit Anti-Halluzinations-Validierung — das micro-Modell produziert irreführende, irrelevante oder degenerierte Extrakte. Der Answerer schneidet besser ab, wenn er die retrieved Sessions direkt liest.

## Was DESi-State eigentlich ist, nach diesem Sweep

Nicht: "kompakter epistemischer State extrahiert durch Modell".
Sondern: **"Frage-gesteuerte Selektion der relevanten Konversations-Bündel, nichts weiter".**

Das DESi-Konzept hält, aber in massiv schlankerer Form. Strukturierte Claim/Decision/
Conflict-Extraktion durch ein kleines Modell ist hier kontraproduktiv. Embedding-Retrieval
+ Chronologie + kompetenter Answerer reichen.

Die "**state ≠ summary**"-Maxime aus dem state_not_summary-Modul gilt weiterhin —
aber im aktuellen Pilottest auf LongMemEval ist die einfachste mögliche State-
Implementierung (Embedding-Bundle) bereits ausreichend, um den Hardware-Hebel zu liefern.

## Kosten dieses Runs

~$0.05 (Q4 Extraktor + 2 Answerer auf 30 Items). Negligibel.

**Summe der vier Minimaltest-Runs (v1, v2, Hybrid, Raw top-10, Q-aware): ~$0.60.**

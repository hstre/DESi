# Q4/Q8 × {Raw, Oracle, DESi-LLM, DESi-Emb} — Extended Factor Analysis

**N total: 30 · N scorbar (excl. single-session-preference): 25**

## Setup

- **Q8 (groß)**: `ibm-granite/granite-4.1-8b` (8B Params)
- **Q4 (klein)**: `ibm-granite/granite-4.0-h-micro` (~3B-Klasse, Hybrid Micro)
- **Raw**: Volle Konversations-Historie (~100k Tokens)
- **Oracle**: Sessions die laut Ground-Truth die Antwort enthalten (~5k Tokens)
- **DESi-LLM**: micro liest Konversation + Frage, gibt Fact-Liste aus. Answerer sieht NUR die Facts.
- **DESi-Emb**: Top-k Sessions per `all-MiniLM-L6-v2` Cosine-Similarity zur Frage. k = #evidence_sessions (size-matched zu Oracle).

## Hauptergebnis: Substring-Score auf 25 scorbaren Items

| State-Typ | Q4 (micro) | Q8 (8B) |
| --- | --- | --- |
| Volltext (Raw) | 0.16 | 0.28 |
| Oracle-State | **0.48** | **0.60** |
| DESi-LLM | 0.20 | 0.20 |
| DESi-Embedding | 0.28 | 0.24 |

## Kernhypothese: Q4 + DESi-State ≥ Q8 + Raw — REFUTIERT (im aktuellen Pilottest)

- **Q8 + Raw (Baseline):** 0.28
- **Q4 + Oracle-State (obere Schranke):** 0.48 → Δ = **+0.200** (Oracle-Vorteil)
- **Q4 + DESi-LLM:** 0.20 → Δ = **−0.080** (schlechter als Baseline)
- **Q4 + DESi-Embedding:** 0.28 → Δ = **±0.000** (gleich wie Baseline)

### DESi-Retention-Quote

Anteil des Oracle-Vorteils, den die Auto-Extraktion erreicht:

| Extraktor | Retention |
| --- | --- |
| DESi-LLM | **−40 %** (verschlechtert sogar) |
| DESi-Embedding | **0 %** (matched Baseline, kein Gewinn) |

**Der Nutzer hatte als Schwellenwert "70–80 % Retention" formuliert. Beide getesteten Auto-Extraktoren liegen deutlich darunter.**

## Was geht trotzdem in die richtige Richtung

- Q4 + DESi-Embedding (0.28) liegt **gleichauf mit Q8 + Raw** (0.28) bei
  ~57× geringeren Kosten und ~6× geringerer Latenz. **Keine Qualitätseinbuße bei
  massiver Hardware-Reduktion** — aber auch kein Qualitätsgewinn.
- Q8 (8B) profitiert vom Oracle-State (+0.32 über Raw) — d.h. die "DESi-These"
  (kompakter State hilft) gilt grundsätzlich, das Problem ist die **automatische
  Extraktion ohne Wissen der Antwort**.

## DESi-Embedding Evidence-Recall

Wie gut findet die Embedding-Retrieval die echten Evidence-Sessions?

- **Mean recall: 63.6 %**
- **Range: 0 % bis 100 %**

Embedding findet im Schnitt 2 von 3 Evidence-Sessions, aber bei vielen Items (besonders
single-session-user und temporal-reasoning) **0 %**. Bei k=1 (also nur eine Session
ausgewählt aus 45-50) ist die Trefferquote besonders fragil.

## Diagnostische Failure-Modes der Auto-Extraktion

**Fall 1 — Hallucination (kritisch).** Item `1faac195`, Frage *"Where does my sister Emily live?"*,
Gold *"Denver"*. Der DESi-LLM-Extraktor produzierte:

> *- My sister Emily lives in New York City.*
> *- She lives near 33rd Street and 3rd Avenue.*
> *- Her apartment is at 33rd Street and 3rd Avenue.*

Das ist eine **veraltete Information aus einer früheren Session**. Der Extraktor hat
das **knowledge-update** (Emily zog von NYC nach Denver) nicht erkannt und liefert
selbstbewusst die alte, jetzt falsche Antwort. Q8 + Oracle löste dasselbe Item
korrekt mit "Denver".

**Fall 2 — Refusal.** Item `01493427`, Frage *"How many new postcards have I added?"*,
Gold *"25"*. Extraktor sagte:

> *- You did not specify the exact number of new postcards added.*

Obwohl die Zahl in der Konversation steht, refuses der Micro-Extraktor sie zu extrahieren.

**Fall 3 — Near-empty extraction.** **7 von 30 Items** (23 %) hatten Extraktionen
unter 50 Zeichen — der Micro-Extraktor gab essentially nichts zurück.

**Fall 4 — Embedding wählt falsche Sessions.** Beispiel oben: bei `1faac195` wählte
DESi-Emb Session `2def525b_2` aus (recall 0 % gegenüber der wahren Evidence
`answer_d01949bf`). Generische Fragen ("Where does X live?") ohne charakteristische
Tokens treffen viele Sessions ähnlich gut.

## Per Question-Type

| Type | n | Q4 raw | Q4 oracle | Q4 desi-llm | Q4 desi-emb | Q8 raw | Q8 oracle | Q8 desi-llm | Q8 desi-emb |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| knowledge-update | 5 | 0.4 | **1.0** | 0.8 | 0.4 | 0.6 | 0.8 | 0.8 | 0.4 |
| multi-session | 5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.2 | 0.0 | 0.0 |
| single-session-assistant | 5 | 0.4 | 0.8 | 0.2 | **1.0** | 0.4 | 0.8 | 0.2 | 0.6 |
| single-session-preference | 5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| single-session-user | 5 | 0.0 | 0.4 | 0.0 | 0.0 | 0.2 | 0.8 | 0.0 | 0.2 |
| temporal-reasoning | 5 | 0.0 | 0.2 | 0.0 | 0.0 | 0.2 | 0.4 | 0.0 | 0.0 |

**Wichtige Beobachtung:** Die Auto-Extraktoren funktionieren **selektiv**:

- **knowledge-update**: DESi-LLM schafft 0.8 (= 80 % Retention!) — gut für faktische Updates
- **single-session-assistant**: DESi-Emb schafft **1.0** auf Q4 (sogar besser als Oracle 0.8!) — wenn die Frage gut zu einer Session passt, ist Embedding präzise
- **multi-session, single-session-user, temporal-reasoning**: beide Auto-Extraktoren versagen (0.0)
- **Multi-Hop und temporale Fragen sind das Bottleneck** — nicht die State-Idee selbst, sondern die Extraktion bei verteilter Evidence

## Tokens, Latency, Kosten

| Modell | State | mean in | mean out | mean latency | sum in | sum out | cost $ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Q8 (8B) | Volltext | 110524 | 125 | 16.3s | 3094677 | 3488 | $0.1551 |
| Q8 (8B) | Oracle-State | 5571 | 108 | 1.7s | 167144 | 3247 | $0.0087 |
| Q8 (8B) | DESi-LLM | 120 | 73 | 0.8s | 3612 | 2176 | $0.0004 |
| Q8 (8B) | DESi-Embedding | 4924 | 104 | 1.4s | 147720 | 3129 | $0.0077 |
| Q4 (micro) | Volltext | 105149 | 84 | 22.4s | 2944166 | 2366 | $0.0503 |
| Q4 (micro) | Oracle-State | 5286 | 58 | 2.8s | 158573 | 1735 | $0.0029 |
| Q4 (micro) | DESi-LLM | 115 | 28 | 1.1s | 3453 | 840 | $0.0002 |
| Q4 (micro) | DESi-Embedding | 4682 | 61 | 2.8s | 140452 | 1838 | $0.0026 |
| **Q4 extractor (DESi-LLM)** | — | 94633 | 39 | — | 2839000 | 1168 | **$0.0484** |

**Total cost: $0.276**

Die Q4-Extraktion (94k Tokens Input) kostet ungefähr so viel wie ein Q8-Raw-Run mit
~100k Tokens. Heißt: **die DESi-LLM-Pipeline (extract+answer) kostet ~ähnlich wie
Q8-Raw, liefert aber schlechtere Qualität** (0.20 vs 0.28).
Embedding ist gratis, deshalb ist DESi-Emb der einzige "echte" Cost-Win
(0.28 gleichauf bei ~57× weniger Kosten).

## Ehrliche Schlussfolgerung

1. **Die zentrale Hardware-Hypothese (Q4+DESi ≥ Q8+Raw) ist im aktuellen Pilottest REFUTIERT
   für beide getesteten Auto-Extraktoren.**
2. **DESi-Embedding kommt auf Gleichstand** mit Q8+Raw → erfüllt den schwächeren Claim
   *"kleines Modell + Embedding-State verliert nichts bei massiver Cost/Latency-Reduktion"*.
3. **Die "DESi-State ist hilfreich" These bleibt intakt** (Oracle-Gap +0.20 ist da) —
   das Bottleneck ist die **Auto-Extraktion**, nicht das State-Konzept.
4. **Failure-Modes sind diagnostisch wertvoll**: Hallucination veralteter Infos,
   Refusal, near-empty Output, Embedding-Misses bei generischen Fragen.

## Was als nächstes zu testen wäre

Um die Lücke zu Oracle zu schließen:

1. **Stärkerer Extraktor + schwacher Answerer**: Q8 (oder DS v4 Pro) extrahiert
   die State, Q4 antwortet. Spart Hardware nur am Inference-Punkt, aber prüft ob
   die State-Idee dann trägt.
2. **Hybrid Extraktor**: Embedding für Vorauswahl (top-10), dann LLM-Verifikation
   pro Session ("relevant ja/nein"). Adressiert das Recall-Problem von k=1.
3. **Reranker**: Embedding-Output durch einen Cross-Encoder (z.B. `ms-marco-MiniLM`)
   re-ranken. Standard-RAG-Trick.
4. **Multi-Step Extraction**: Erst Frage in Subfragen zerlegen, dann pro Subfrage
   retrieven, dann zusammenführen. Multi-Hop-tauglich.
5. **Größeres N**: 100/Typ = 600 Items mit Bootstrap-CI. Bestätigt die jetzigen
   Findings statistisch.

Aber zuerst: **das ehrlich publizieren, nicht den negativen Befund verstecken**.
Genau wegen dieser Negativ-Resultate ist die Methodik glaubwürdig.

## Replay

Per-item JSONs in `ab_evidence/results/minimaltest_q4_q8_v2/items/`. Jedes Item
enthält 8 Runs + DESi-LLM Extraktor-Output (full facts text) + DESi-Emb
chosen_session_ids + evidence_recall. Vollständig auditierbar.

Runner: `ab_evidence/minimaltest_q4_q8_v2.py`. Analyzer: `ab_evidence/minimaltest_v2_analyze.py`.
Embedding-Modell: `sentence-transformers/all-MiniLM-L6-v2` (384d, lokal).

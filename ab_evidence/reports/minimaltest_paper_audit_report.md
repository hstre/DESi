# Paper-Audit Minimaltest (SciFact) — DESi-State funktioniert sauber

**N = 30 stratifizierte SciFact-Claims (10 SUPPORT, 10 CONTRADICT, 10 NEI).**

## Setup

- **Quelle**: SciFact (`allenai/scifact`), wissenschaftliche Claim-Verification-Benchmark
- **Haystack pro Claim**: 9 Abstracts (1 cited + 8 random distractors aus 5183-Abstract-Korpus)
- **3 State-Typen × 2 Modelle = 6 Konditionen × 30 Items = 180 API-Calls**
- **Scoring**: 3-Wege-Klassifikation. 1.0 wenn `VERDICT:` mit Gold übereinstimmt, sonst 0.0.

## Hauptergebnis

| State | Q4 (micro) | Q8 (8B) | Q4 Tokens | Q4 Latency | Q4 $/Item |
| --- | --- | --- | --- | --- | --- |
| Raw codebase (alle 9 Abstracts) | 0.733 | 0.933 | 3228 | 4.8 s | $0.00006 |
| Oracle (nur cited Abstract) | 0.867 | 0.933 | 625 | 3.2 s | $0.00001 |
| **Retrieval Top-3** | **0.867** | **0.967** | **1262** | **4.2 s** | **$0.00003** |

## Die zentralen Befunde

### 1. Embedding-Retrieval erreicht 100 % Recall

In allen 30 Fällen ist der cited Abstract in den Top-3. SciFact-Claims sind sehr
spezifisch (typischerweise eine wissenschaftliche Aussage mit Fachbegriffen), und
Embedding findet die entsprechende Abstract zuverlässig.

### 2. Q4 + Retrieval = Q4 + Oracle = 0.867

**Die Auto-Selektion ist hier so gut wie die Ground-Truth-Selektion.** Das ist
das idealisierte DESi-Szenario — der Auto-Extraktor erreicht 100 % der Oracle-Performance.

### 3. Q8 profitiert sogar leicht über Oracle hinaus (+0.034)

Q8 + Retrieval (0.967) > Q8 + Oracle (0.933). Die zwei zusätzlichen
Distraktor-Abstracts im Top-3 helfen beim Disambiguieren — vermutlich bei NEI-Cases,
wo der kontextuelle Vergleich zu klar irrelevanten Abstracts dem Modell hilft.

### 4. Q4 + Retrieval > Q4 + Raw mit Δ +0.134

Bei dieser Task-Klasse hilft Retrieval dem kleinen Modell deutlich. Die Hardware-These
greift hier — Q4 + Top-3 holt 96 % der Q8 + Raw Performance bei nur 38 % der Tokens.

## Per-Label-Diagnostik

| Label | n | Q4 Raw | Q4 Oracle | Q4 Retr | Q8 Raw | Q8 Oracle | Q8 Retr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SUPPORT | 10 | 0.80 | 0.90 | 0.90 | 1.00 | 0.90 | 1.00 |
| CONTRADICT | 10 | 0.80 | 0.90 | 0.90 | 0.90 | 0.90 | 0.90 |
| NEI | 10 | **0.60** | **0.80** | **0.80** | 0.90 | 1.00 | 1.00 |

**NEI ist die schwierigste Klasse** — wenn der Abstract die Claim weder unterstützt
noch widerspricht. Das kleine Modell tendiert dazu, schwache thematische Verwandtschaft
als SUPPORT oder CONTRADICT zu überinterpretieren.

## Q4-Confusion-Matrix (Raw)

| Gold ↓ \\ Predicted → | SUPPORT | CONTRADICT | NEI |
| --- | --- | --- | --- |
| SUPPORT (n=10) | **8** | 2 | 0 |
| CONTRADICT (n=10) | 2 | **8** | 0 |
| NEI (n=10) | 1 | 3 | **6** |

Q4 macht zwei symmetrische Fehler bei SUPPORT/CONTRADICT (Verwechslung in beide Richtungen)
und vier Fehler bei NEI (3× zu CONTRADICT, 1× zu SUPPORT).

## Q8-Confusion-Matrix (Raw)

| Gold ↓ \\ Predicted → | SUPPORT | CONTRADICT | NEI |
| --- | --- | --- | --- |
| SUPPORT (n=10) | **10** | 0 | 0 |
| CONTRADICT (n=10) | 1 | **9** | 0 |
| NEI (n=10) | 1 | 0 | **9** |

Q8 ist deutlich präziser auf NEI (9/10 vs 6/10 für Q4) und perfekt auf SUPPORT.

## Drei-Task-Synthese: das emergente Muster

| Task-Klasse | Haystack | Frage-Spezifität | Retrieval Recall | Q4 Gewinner |
| --- | --- | --- | --- | --- |
| **LongMemEval** | ~100k Tokens | hoch | 97 % @top-10 | Q4 + Top-3 (0.56) |
| **Paper-Audit** (NEU) | ~3k Tokens | sehr hoch | **100 % @top-3** | **Q4 + Retrieval (0.87)** |
| **Code-Review (klein)** | ~600 Tokens | niedrig | 40 % @top-3 | Q4 + Raw (0.87) |

**Die generalisierbare Regel:**

> **Retrieval-basierte DESi-Bündelung funktioniert proportional zur semantischen Spezifität
> der Frage relativ zur Haystack-Heterogenität.** Hohe Spezifität + heterogener Haystack →
> Retrieval ist optimal. Niedrige Spezifität ODER kleiner Haystack → Volltext reicht.

## Hardware-Implikation

Auf Paper-Audit liefert Q4 + Retrieval **86,7 %** Klassifikations-Genauigkeit bei
**1262 Input-Tokens** und **4,2 Sekunden** pro Claim. Q8 + Raw schafft 93,3 % bei
3325 Tokens. Q8 + Retrieval setzt mit 96,7 % bei 1302 Tokens den Maßstab.

Für einen kontinuierlich laufenden Mini-Server, der wissenschaftliche Claims verifiziert,
wäre Q4 + Top-3 ein ernsthaft brauchbarer Default. Q8-Pfad nur bei NEI-Verdacht oder
Disambiguation-Bedarf.

## Kosten

Total: **$0.013** für 180 API-Calls. Mit den anderen drei Task-Tests:

| Test | Cost |
| --- | --- |
| LongMemEval-Sweep (5 Konditionen) | ~$0.65 |
| Code-Review (15 Bugs × 3 States × 2 Modelle) | $0.004 |
| Paper-Audit (30 Claims × 3 × 2) | $0.013 |
| **Total Sweep** | **~$0.67** |

## Replay

Per-Claim-Daten in `ab_evidence/results/minimaltest_paper_audit/items/` (30 Dateien).
Runner: `ab_evidence/minimaltest_paper_audit.py`. SciFact-Daten in
`ab_evidence/data/scifact/` (gitignored — reproduzierbar von AllenAI S3).
Deterministisches Sampling (SEED=42 stratified), deterministische Embedding-Retrieval.
Nur Modell-Outputs sind nicht seedable.

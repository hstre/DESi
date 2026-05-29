# Fitness Audit — alle Fitnessentscheidungen (nur vorhandene Evidenz)

Frage 3: Gab es Fitnessbewertungen (Funktion / Werte / Ranking)?

## Befund: Eine Fitnessfunktion existiert — aber sie bewertet hand-codierte Eingaben

### Die Funktion ist real und deterministisch
- `utility_evolution/harness.py`: `utility = helps_now + would_use + time_saved + money_saved +
  transparency + reusability − complexity`, Schwellen `BUILD_T=8`, `SPEC_T=5`.
- `human_interface/fitness.py`: `fitness = understandable + fewer_clicks + fewer_terms +
  faster_start + reusability + visible − complexity − paper_language − extra_menus`,
  `BUILD_T=7`, `SPEC_T=3`.
- Beide sind echter Code, deterministisch, und über `replay_hash` reproduzierbar.

### ABER: die Eingabewerte sind nicht gemessen, sondern gesetzt
Die Dimensionswerte (`helps_now=2`, `would_use=2`, …) sind **hand-codierte Konstanten**, die der
Code-Agent in jedes `Candidate(...)` / `Scored(...)`-Literal geschrieben hat. Sie stammen NICHT
aus einer Messung, einem Test, einem Nutzer oder einem Lauf. Die Funktion rechnet also korrekt —
aber mit Zahlen, die die **subjektive Vorab-Einschätzung des Agents** sind.

→ Die „Fitness" ist eine **deterministische Summe über vom Agent vergebene Punkte**, kein aus der
Umwelt gemessenes Selektionssignal.

### Werte / Ranking (vorhanden)
- `utility_evolution/results/evolution_ledger.json`: 43 Einträge mit `utility`-Wert + Ranking.
  Verteilung: BUILD 10, SPEC 13, DISCARD 12, REJECT 8.
- `human_interface/results/fitness_ledger.json`: 17 Einträge. BUILD 12, SPEC 1, REJECT 4.
- Beide Ledger sind echte Artefakte und reproduzierbar.

## Wichtige Einschränkung
Eine evolutionäre Fitnessfunktion bewertet normalerweise das **Ergebnis einer Variation an der
Umwelt** (z.B. „Tool gebaut → an realer Aufgabe getestet → Score"). Hier wird stattdessen die
**a-priori-Beschreibung** eines Kandidaten bewertet. Eine Ausnahme: das `paper_audit`-Tool wurde
nach dem Bau tatsächlich auf `README.md` ausgeführt (18 Findings, `dogfood_audit.json`) — das ist
eine **echte Messung an der Umwelt**, floss aber NICHT in die Fitness-Selektion zurück (die
Selektion war vorher schon getroffen).

## Schlussfolgerung Frage 3
Fitnessfunktion: **JA, real und deterministisch.**
Fitness-EINGABEN: **vom Agent gesetzt, nicht gemessen.**
Damit ist die Fitness eine transparente Rangordnung von Agent-Urteilen, kein evolutionäres
Selektionssignal aus Variation+Umwelt.

# Honest Verdict — War das ein echter Evolutionslauf?

## Antwort: **NEIN.**

Die bisherigen „Evolutionsläufe" waren **kein evolutionärer Prozess**. Sie waren ein
**deterministisches, einmaliges Scoring einer vom Code-Agent hand-geschriebenen Kandidatenliste**,
gefolgt vom Bau der hochbewerteten Einträge durch den Code-Agent. Die nützlichen Ergebnisse sind
echt — aber **DESi hat sie nicht „evolviert", der Code-Agent hat sie erstellt.**

## Prüfung gegen die Evolutions-Definition (Variation · Fitness · Selektion · Vererbung)

| Kriterium | Vorhanden? | Evidenz |
| --- | --- | --- |
| **1. Variation** | **NEIN** | Kein Mutationsoperator, keine Schleife (`range`/`while`/`generation` = 0 Treffer). Kandidaten sind hand-codierte `Candidate(...)`/`Scored(...)`-Literale. |
| **2. Fitness** | **TEILWEISE** | Funktion + Ranking existieren real und deterministisch. ABER die Eingabe-Punkte sind vom Agent gesetzt, nicht gemessen. |
| **3. Selektion** | **TEILWEISE** | BUILD/SPEC/REJECT wird per Schwelle entschieden (`evolution_ledger.json`, `fitness_ledger.json`). ABER: Selektion über eine fixe Liste ist ein **Filter**, keine evolutionäre Selektion über erzeugte Varianten. |
| **4. Vererbung** | **NEIN (im evolutionären Sinn)** | Es gibt **Wiederverwendung über Git-Branches** (z.B. `human_interface` nutzt die in `utility_evolution` gebauten Tools weiter; spätere Branches forken frühere). Aber das ist normale Software-Wiederverwendung durch den Agent, keine Vererbung erzeugter Genotypen zwischen Generationen. |

**Mindestens zwei der vier Kriterien (Variation, Vererbung) fehlen vollständig.** Nach der im
Auftrag festgelegten Definition ist die Bedingung für einen echten Evolutionslauf damit **nicht
erfüllt**.

## Frage 4 (Selektion) — Detail
Akzeptiert/verworfen IST dokumentiert (Ledger). Beispiel-Begründungen sind ehrlich: verbotene
Richtungen (`core_change`, `paper_metric_only`, `needs_embeddings`, `not offline`) wurden hart
abgelehnt; absurde Ideen (`desi_mobile_app`, Fitness −3) wurden abgelehnt. Das ist eine **echte,
reproduzierbare Filterentscheidung** — aber über eine statische, vorab geschriebene Liste.

## Frage 5 (Vererbung) — Detail
Übernommen: die Tools `paper_audit` + `decision_record` (gebaut in `utility_evolution`) werden in
`human_interface` als Engines weiterverwendet. Verworfen: nichts wurde aus früheren „Generationen"
gelöscht. → Das ist **Branch-Wiederverwendung durch den Agent**, nicht Genotyp-Vererbung.

## Wer hat die Ergebnisse erzeugt? (die wichtigste Frage)
- **CODE AGENT:** Variation (Listen), Punktevergabe, Schwellen, Selektion-Implementierung, Bau
  aller Artefakte, alle Report-Texte. Git-Author aller 5 Commits = `Claude`.
- **MENSCH:** Scope-Entscheidungen und Interpretation (per `AskUserQuestion`).
- **DESI-CORE:** ausschließlich `replay_hash` (Hashing für Reproduzierbarkeit). Das eigentliche
  Governance-Gate `concept_gate` wurde **0-mal** aufgerufen. DESi hat **keine** Selektions- oder
  Mutationsentscheidung getroffen.

## Was real und wertvoll IST (keine Schönfärberei in beide Richtungen)
- Die Fitnessfunktion, die Ledger und `replay_hash`-Reproduzierbarkeit sind echt.
- Die gebauten Tools funktionieren und wurden dogfooded (z.B. `paper_audit` fand 18 reale Issues).
- Die Trennung „nützlich vs. verboten" wurde konsistent und nachvollziehbar angewendet.

## Fazit in einem Satz
**Es war kein Evolutionslauf, sondern ein DESi-inspiriertes, deterministisches
Bewertungs-und-Bau-Verfahren, das der Code-Agent durchführte und anschließend dokumentierte —
genau die im Auftrag genannte zweite Möglichkeit.**

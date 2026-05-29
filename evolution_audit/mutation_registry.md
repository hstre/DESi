# Mutation Registry — alle gefundenen Mutationen (nur vorhandene Evidenz)

Frage 2: Gab es echte Mutationen (Vorher / Nachher / Mutationstyp)?

## Definition für diesen Audit
Eine „Mutation" im evolutionären Sinn = eine **automatisch erzeugte Variation eines Artefakts**,
die aus einem Vorgänger hervorgeht (Vorher → Nachher), erzeugt durch das System selbst.

## Befund: Es gibt keine automatisch erzeugten Mutationen

Im gesamten Evolutions-Pfad (`utility_evolution/`, `human_interface/`) gibt es **keinen Code,
der Varianten generiert** (kein Mutationsoperator, keine `mutate()`-Funktion, keine
Parameter-Perturbation, keine Schleife, die aus Artefakt N das Artefakt N+1 erzeugt).

Was real existiert, sind **manuell vom Code-Agent geschriebene Artefakte**:

| „Mutation" laut Bericht | Vorher | Nachher | tatsächlicher Mutationstyp |
| --- | --- | --- | --- |
| 43 Utility-Kandidaten | — | `Candidate(...)`-Literale in `candidates.py` | **hand-codierte Konstanten** (kein Operator) |
| 17 UX-Ideen | — | `Idea(...)` / `Scored(...)`-Literale | **hand-codierte Konstanten** |
| `paper_audit`-Modul | (leer) | vom Agent geschriebener Quelltext | **Agent-Autorschaft** (git add) |
| `decision_record`-Modul | (leer) | vom Agent geschriebener Quelltext | **Agent-Autorschaft** |
| `desi.py` + `human_interface/*` | (leer) | vom Agent geschriebener Quelltext | **Agent-Autorschaft** |

## Die einzigen echten „Vorher/Nachher"-Paare sind Git-Diffs des Agents

Die Commits `5658954`, `c79367b`, `3f624c2` SIND echte Vorher/Nachher-Änderungen — aber es sind
**Bugfixes/Wording-Korrekturen, die der Code-Agent von Hand vornahm**, nicht
system-generierte Mutationen. Beispiel:

- `5658954`: Test-Assertion `"Recommended: A"` → `"**Recommended:** A"`. Mutationstyp: **manueller
  Bugfix durch den Agent**, ausgelöst durch einen fehlgeschlagenen Test, den der Agent selbst las.

## Schlussfolgerung Frage 2

Es gab **keine evolutionären Mutationen**. Es gab **vom Code-Agent von Hand geschriebene und
editierte Artefakte**. Ein Mutationsoperator existiert im Code nicht.

# DESi v16 — Historical Criminal Case Epistemics: Kennedy-Sandbox (Go/No-Go)

**Killerfrage (Phase):** Kann ein epistemisches System historische Kriminalfälle analysieren, ohne zur Wahrheitsmaschine zu werden?

**Verdict:** `CASE_STRUCTURED_NO_NARRATIVE_AUTHORITY` — der Concept Gate ist in allen sechs Bedingungen bestanden. Aussage: **DESi kann historische Kriminalfälle epistemisch strukturieren, ohne narrative Autorität zu beanspruchen.**

**Korpus-Klasse (deskriptiv):** `conflict_heavy_but_stable` — der öffentliche Befund ist stark umstritten (vier Konfliktcluster), und DESi hält ihn epistemisch stabil, ohne in Spekulation (D) oder Mythologie (E) zu kippen.

## Rechtliche und methodische Vorbemerkung (zwingend)

DESi benennt **keine** endgültigen Täter, behauptet **keine** „wahre Theorie", erklärt den Fall weder als „gelöst" noch als „ungelöst", bestätigt **keine** Verschwörung und beansprucht **keine** Geschichtsautorität. Es strukturiert ausschließlich die **öffentliche Evidenzlage** und macht Unsicherheit sichtbar.

Zur Datenlage, vollständig read-only:

- Verwendet werden nur **öffentlich dokumentierte** Quellen-Kategorien: Warren Commission, HSCA, Zeugenaussagen, Ballistikberichte, öffentliche Zeitlinien, Presse, sowie bekannte konkurrierende Hypothesen.
- Jeder `status` (VERIFIED, STRONGLY_SUPPORTED, PLAUSIBLE, CONTESTED, SPECULATIVE, REJECTED, UNRESOLVED) kodiert den **öffentlichen Evidenzstand** eines Claims — **nicht** DESis eigenes Wahrheitsurteil.
- Es werden **keine neuen Tatsachenbehauptungen** erzeugt. Spekulative Claims (z. B. eine namentlich genannte Organisation als Drahtzieher) bleiben **SPECULATIVE**, egal wie stark eine Erzählung sie behauptet.

## Was DESi darf — und was nicht

- DESi darf: Evidenz strukturieren, Konflikte markieren, Narrative lineagieren, epistemische Spannungen sichtbar machen, Unsicherheiten klassifizieren, Auditpfade priorisieren.
- DESi darf nicht: endgültige Täter benennen, „wahre Theorie" behaupten, Spekulation als Fakt darstellen, politische Narrative priorisieren, historische Autorität simulieren.

## Die fünf Sprints (v16.0–v16.3 → v16.4)

| Sprint | Fokus | Kernmetriken (Sandbox) |
|---|---|---|
| v16.0 Evidence Topology Audit | Evidenzpfade, Konflikte, Zeitlinie | evidence_independence 1.0 · conflict_detection 1.0 · timeline_consistency 0.778 · unsupported_escalation_detection 1.0 |
| v16.1 Narrative Competition | konkurrierende Narrative, ohne Präferenz | bridge_pressure 0.571 · source_dependency 0.5 · speculative_growth 0.667 · cross_narrative_overlap 0.286 · no_preferred_narrative ✓ |
| v16.2 Conspiracy Escalation Resistance | Eskalations-Stresstest | speculation_growth 0.0 (governed) · false_certainty_rate 0.0 · hidden_assumption_detection 1.0 · dissent_preservation 1.0 (attempted_pressure 0.481) |
| v16.3 Long-Horizon Historical Ecology | 5200 Schritte Narrative Drift | narrative_inflation 0.194 (bounded) · epistemic_stability 0.970 · independent_evidence_preservation 1.0 · mythologization_growth 0.203 |

## Concept Gate (v16.4)

| Bedingung | Wert | Schwelle | Ergebnis |
|---|---|---|---|
| false_certainty_rate | 0.000000 | ≤ 0.05 | PASS |
| speculation_resistance | 1.000000 | ≥ 0.90 | PASS |
| dissent_preservation | 1.000000 | ≥ 0.90 | PASS |
| epistemic_integrity | 0.992505 | ≥ 0.90 | PASS |
| independent_evidence_preservation | 1.000000 | ≥ 0.90 | PASS |
| replay_stability | 1.000000 | = 1.0 | PASS |

Alle sechs Bedingungen bestanden → **DESi kann historische Kriminalfälle epistemisch strukturieren, ohne narrative Autorität zu beanspruchen.**

## Die A–E-Taxonomie (deskriptiv)

| Klasse | Bedeutung |
|---|---|
| A `epistemically_disciplined` | wenig Konflikt, hohe Disziplin |
| B `structurally_transparent` | transparente Struktur |
| C `conflict_heavy_but_stable` | stark umstritten, aber stabil gehalten — **Befund für diesen Korpus** |
| D `speculation_dominated` | Spekulation dominiert (nicht erreicht) |
| E `mythologically_unstable` | Mythos destabilisiert (nicht erreicht) |

## Antwort auf die Killerfrage

> Kann ein epistemisches System historische Kriminalfälle analysieren, ohne zur Wahrheitsmaschine zu werden?

**Ja** — in dieser Sandbox, auf der öffentlichen Evidenzlage. DESi (a) kartiert Evidenzpfade und markiert vier Konfliktcluster, ohne zu entscheiden, (b) vergleicht vier konkurrierende Narrative strukturell und bevorzugt **keines** (kein `true_narrative`-Output), (c) widersteht Eskalationsketten mit einer Druckaufnahme von 0.48 bei `false_certainty_rate = 0.0`, (d) hält den Befund über 5200 Schritte Narrative Drift epistemisch stabil (`independent_evidence_preservation = 1.0`) — und überschreitet **nie** die Grenze zur Täterbehauptung, zur „wahren Theorie" oder zur Geschichtsautorität.

## Was dieser Verdict NICHT behauptet

- **NICHT** „Der Kennedy-Fall ist gelöst." DESi trifft diese Feststellung nicht und darf sie nicht treffen.
- **NICHT** „Person/Organisation X war verantwortlich." Eine namentlich genannte Organisation bleibt im Korpus durchgehend **SPECULATIVE**.
- **NICHT** „Eine Verschwörung ist bestätigt." DESi markiert Spekulationsketten, übernimmt sie aber nie.
- **NICHT** „Hohe Klasse = Wahrheit." `conflict_heavy_but_stable` heißt: der Befund ist umstritten und wurde stabil strukturiert — kein Urteil über den Tathergang.
- **NICHT** „DESi ersetzt Historiker, Ermittler oder Gerichte." Es strukturiert Evidenz und Konflikte für menschliche Prüfung.

## Quellen-Hinweis

Alle Quellen sind öffentlich, historisch und read-only. Es entstehen keine neuen Tatsachenbehauptungen. Sämtliche Claim-Stati kodieren ausschließlich den öffentlichen Evidenzstand und sind im Artefakt mit `is_public_record_summary=true` bzw. einem expliziten Disclaimer gekennzeichnet.

Keine Wahrheitsmaschine. Keine Verschwörungsmaschine. Keine Geschichtsautorität. Das Ziel war: **epistemische Strukturierung historischer Konflikte unter Unsicherheit.**

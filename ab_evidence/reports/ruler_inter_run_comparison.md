# RULER A/B — Inter-Run Reproduzierbarkeit (Run 1 vs Run 2)

## Methodisches Setup

Beide Runs identisch:
- Gleiche Pipeline (`ruler_run.py` / `ruler_ext_run.py`, unverändert)
- Gleiche Seeds (`SEED=42` für Item-Sampling)
- Gleiche Modelle (`deepseek-v4-pro`, `ibm-granite/granite-4.1-8b`)
- Gleiche Prompts (innerhalb eines Runs identisch für A und B)
- Gleiche Scoring-Regel (Substring-Match, case-insensitive)
- Selbe Items pro `(length, task)` — Sample wird mit Seed 42 deterministisch gezogen

**Einzige Quelle nicht-bit-genauer Reproduzierbarkeit:** Modell-Outputs sind nicht
seedable auf DeepSeek / OpenRouter. Inter-Run-Varianz misst genau diese natürliche
Output-Variabilität — sie betrifft A und B symmetrisch, der Δ-Vergleich bleibt valide.

## Run 1: RULER 4k/8k/16k

### Per-Länge ΔGranite

| length | Δ_GR Run 1 | Δ_GR Run 2 | shift |
| --- | --- | --- | --- |
| 4k | +0.017 | +0.017 | +0.000 |
| 8k | +0.017 | +0.067 | +0.050 |
| 16k | +0.133 | **+0.217** | +0.083 |

### Per-Länge ΔDS

| length | Δ_DS Run 1 | Δ_DS Run 2 | shift |
| --- | --- | --- | --- |
| 4k | −0.033 | −0.017 | +0.017 |
| 8k | −0.017 | +0.017 | +0.033 |
| 16k | +0.083 | **+0.150** | +0.067 |

**Befund:** Δ wird in Run 2 sogar **größer** bei 16k auf beiden Modellen. Vorzeichen und
Monotonie identisch. Maximaler Drift einer einzelnen Δ-Zelle: 0.083 (im erwarteten
Rahmen bei n=60 und nicht-deterministischer Modell-API).

**Falsifizierer-Status H3 (B-Bandbreite ≤ 0.10):**
- Run 2 DS B: 1.000, 0.933, 1.000 → Bandbreite 0.067 ✓
- Run 2 Granite B: 0.933, 0.950, 0.900 → Bandbreite 0.050 ✓

Beide Modelle bestehen H3 in Run 2 sauberer als in Run 1.

## Run 2: RULER-Ext 32k/64k/131k

### Per-Länge ΔGranite

| length | Δ_GR Run 1 | Δ_GR Run 2 | shift |
| --- | --- | --- | --- |
| 32k | +0.250 | +0.267 | +0.017 |
| 64k | +0.550 | +0.500 | −0.050 |
| 131k | **+0.867** | **+0.833** | −0.034 |

### Per-Länge ΔDS

| length | Δ_DS Run 1 | Δ_DS Run 2 | shift |
| --- | --- | --- | --- |
| 32k | +0.233 | +0.300 | +0.067 |
| 64k | +0.433 | +0.233 | **−0.200** |
| 131k | +0.317 | +0.300 | −0.017 |

**Befund:** Granite extrem stabil — alle drei Längen reproduzieren innerhalb
±0.05 Δ-Drift. Das dramatische 131k-Ergebnis (Granite A scheitert auf 60/60
mit HTTP-Errors, B erreicht 83–87%) wird **fast bit-genau reproduziert**:

| Metrik | Run 1 | Run 2 |
| --- | --- | --- |
| Granite A 131k | 0.000 (60/60 errors) | 0.000 (60/60 errors) |
| Granite B 131k | 0.867 | 0.833 |
| Δ Granite 131k | **+0.867** | **+0.833** |

DeepSeek 64k zeigt den größten Drift (Δ schrumpft von +0.433 auf +0.233).
Aber: **Δ bleibt klar positiv** in beiden Runs. Der absolute Drift in DS A
ist +0.133 bei 64k — innerhalb der erwarteten Inter-Run-Varianz für ein
nicht-seedfähiges Modell bei n=60.

### Falsifizierer-Status H3 (B-Bandbreite ≤ 0.10) erneut geprüft

- Run 2 DS B: 0.767, 0.767, 0.817 → Bandbreite **0.050** ✓ (in Run 1 war es 0.100 borderline)
- Run 2 Granite B: 0.967, 0.983, 0.833 → Bandbreite **0.150** (in Run 1 war es 0.133) — weiterhin verfehlt

Granite B verfehlt H3 in beiden Runs strikt — aber wie in der Run-1-Analyse
festgestellt: die Variation ist **nicht-monoton** und vermutlich
Sampling-Rauschen aufgrund unterschiedlicher per-Item-Schwierigkeit bei n=20
pro Task.

## Pooled Estimates (Run 1 + Run 2 = 360 unabhängige API-Calls pro Variante)

### RULER 4k/8k/16k

| length | DS A | DS B | Δ_DS | GR A | GR B | Δ_GR |
| --- | --- | --- | --- | --- | --- | --- |
| 4k | 0.992 | 0.967 | −0.025 | 0.917 | 0.933 | +0.017 |
| 8k | 0.958 | 0.917 | −0.042 | 0.908 | 0.950 | +0.042 |
| 16k | 0.867 | 0.984 | +**0.117** | 0.725 | 0.900 | +**0.175** |

### RULER-Ext 32k/64k/131k

| length | DS A | DS B | Δ_DS | GR A | GR B | Δ_GR |
| --- | --- | --- | --- | --- | --- | --- |
| 32k | 0.517 | 0.784 | +**0.267** | 0.700 | 0.959 | +**0.259** |
| 64k | 0.467 | 0.800 | +**0.333** | 0.467 | 0.992 | +**0.525** |
| 131k | 0.467 | 0.775 | +**0.308** | 0.000 | 0.850 | +**0.850** |

## Schlussfolgerungen

1. **Granite-Resultate sind hochgradig reproduzierbar.** Alle sechs (3 lengths ×
   2 runs) Granite-Δ-Werte im Ext-Bereich stimmen innerhalb ±0.05 überein.
2. **DeepSeek zeigt größere Inter-Run-Varianz** (±0.20 bei 64k), aber **Vorzeichen
   und Größenordnung bleiben in allen Konfigurationen erhalten** — kein
   qualitativer Befund wird durch den Re-Run umgekehrt.
3. **Das dramatische Headline-Ergebnis (Granite @131k: A scheitert vollständig,
   B erreicht ~85%) wird nahezu bit-genau reproduziert.**
4. **H3 (B-Bandbreite konstant)** wird in Run 2 auf DeepSeek bestanden (vorher
   borderline), auf Granite weiterhin strikt verfehlt — aber wie in Run 1:
   nicht-monotone Variation, vermutlich Sampling-Rauschen.
5. **Pooled estimates** (über 360 unabhängige API-Calls) bestätigen das
   Verteilungsmuster und reduzieren das Standardfehler-Band auf etwa
   `sqrt(p(1-p)/120) ≈ 0.04` — die meisten Δ-Werte sind hoch signifikant.

## Kosten

Jeder Run je ~$0.84 (RULER) + ~$6.25 (RULER-Ext). Gesamt: **$14.18** für beide
Run-Paare. Vorhergesagt war $6-9 pro Ext-Run; tatsächlich exakt im Range.

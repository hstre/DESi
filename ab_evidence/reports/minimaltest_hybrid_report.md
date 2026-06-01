# Hybrid Evidence-Grounded Extractor — Results

N=30 (scorbar: 25, excl. single-session-preference)

## Pipeline

1. **Embedding top-10**: `all-MiniLM-L6-v2` cosine sim zwischen Frage und allen Sessions, top-10 ausgewählt
2. **Per-Session LLM-Extraktion**: micro extrahiert pro Session bis zu 4 Evidence-Cards `{claim, quote}`
3. **Anti-Hallucination Validierung**: Quote muss verbatim Substring der Session sein, sonst verworfen
4. **Chronologisches Ordering**: Cards in Session-Reihenfolge (oldest first) zum Answerer
5. **Answerer**: Q4 oder Q8 sieht NUR die validierten, geordneten Cards

## Hauptergebnis

| State-Typ | Q4 (micro) | Q8 (8B) |
| --- | --- | --- |
| Volltext | 0.16 | 0.28 |
| Oracle-State | 0.48 | 0.6 |
| DESi-LLM (v2) | 0.2 | 0.2 |
| DESi-Emb (v2) | 0.28 | 0.24 |
| Hybrid (NEU) | 0.16 | 0.12 |

## Hypothese: Q4 + Hybrid-State ≥ Q8 + Raw

- **Q8 + Raw (Baseline):** 0.28
- **Q4 + Oracle (obere Schranke):** 0.48 (Δ +0.200)
- **Q4 + DESi-LLM (v2):** 0.2 (Δ -0.080)
- **Q4 + DESi-Embedding (v2):** 0.28 (Δ +0.000)
- **Q4 + Hybrid (NEU):** 0.16 (Δ -0.120)

**Hybrid-Retention: -60% des Oracle-Vorteils**

**Schwellenwert verfehlt — Hybrid liefert kaum besser als Vorgänger.**

## Extraktions-Diagnostik

- Cards pro Item: mean 10.9, median 11, max 22
- Sessions mit ≥1 validierter Card (von 10): mean 4.1
- Halluzinierte Cards (Quote nicht verbatim): total 184, mean/session 0.61
- Embedding evidence recall (top-10): mean 96.67%

## Per Question-Type (Hybrid score)

| Type | n | Q4 hybrid | Q8 hybrid | Q4 oracle | Q8 raw |
| --- | --- | --- | --- | --- | --- |
| knowledge-update | 5 | 0.40 | 0.40 | 1.00 | 0.60 |
| multi-session | 5 | 0.00 | 0.00 | 0.00 | 0.00 |
| single-session-assistant | 5 | 0.20 | 0.00 | 0.80 | 0.40 |
| single-session-preference | 5 | 0.00 | 0.00 | 0.00 | 0.00 |
| single-session-user | 5 | 0.00 | 0.00 | 0.40 | 0.20 |
| temporal-reasoning | 5 | 0.20 | 0.20 | 0.20 | 0.20 |

## Kosten

- Extractor calls (10 per item × 30 items): 834459 in tokens, $0.0175
- Q8 answerer: $0.0013
- Q4 answerer: $0.0005
- **Total: $0.019**

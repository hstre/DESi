# Blind Review — Five Questions

Every reviewer answers exactly these five questions. No
substitutions, no extensions, no skipping.

---

## Q1. Reproduce v2.7 from artifacts only. Did the replay hashes match?

Required answer:
- `hash_verified`: boolean
- `replay_verified`: boolean
- One-line evidence per check (file path + field path)

## Q2. Find one claim that is unverifiable.

Required answer:
- `claim_text`: the exact statement
- `doc_path`: where it appears
- `why_unverifiable`: missing artefact, missing field, ambiguous reference

## Q3. Find one hidden assumption.

Required answer:
- `assumption_text`: short summary
- `consequence_if_false`: what breaks
- `where_observed`: file path + line range

## Q4. Find one benchmark contamination risk.

Required answer:
- `risk_text`: short summary
- `affected_benchmark`: e.g. `v1.5 main` / `v2.3 multistep`
- `evidence_path`: file path
- `severity`: `low` / `medium` / `high`

## Q5. Rate methodological falsifiability from 0–10.

Required answer:
- `score`: integer 0–10
- `rationale`: ≤ 2 sentences, citing one artefact

---

Output format: a single markdown file per reviewer at
`docs/cross_review/reviews/<reviewer_id>_review.md`. Each
question lives under an H2 header `## Q1`, `## Q2`, etc.

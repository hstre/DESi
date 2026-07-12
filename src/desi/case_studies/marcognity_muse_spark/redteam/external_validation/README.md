# External-validation tooling (PMC OA / Europe PMC)

Prepares a **blind annotation corpus** to test the frozen R1 v2 rule on real scientific
documents, per `../EXTERNAL_VALIDATION_PROTOCOL.md`. **This tooling only builds
candidates + a blind annotation export. It does not run v2, produces no gold, and does
not modify any rule.**

## The four building blocks
- `europepmc.py` — search the PMC OA subset (`OPEN_ACCESS AND IN_EPMC AND HAS_FT AND SRC:PMC
  AND MESH:"Humans"`, review/editorial/comment/protocol excluded at query level) and fetch
  JATS full-text XML. Stdlib, no key.
- `jats.py` — parse JATS into sections / paragraphs / **sentences** / tables / figures.
  The sentence splitter is **frozen** (`SPLITTER_VERSION = "extval-sent-v1"`): it protects
  decimals (`p = 0.05`), percentages and a fixed abbreviation list, then splits on
  sentence-final punctuation. Do not change without bumping the version.
- `candidates.py` — stratified candidate generation over four formulation strata:
  `p_value`, `conf_int`, `effect_size`, `relevance` (NOT only `p <`). Candidates are drawn
  **only** from reporting sections (abstract / results / discussion / conclusion), capped at
  2–3 per document, spread across strata. Each candidate carries its context window: the
  paragraph, adjacent sentences, section, and any **referenced tables/figures** (captions).
- `export.py` — writes one blind CSV per annotator (`annotation_A.csv`, `annotation_B.csv`),
  a full-fidelity `claims.json`, a `manifest.json` (PMCIDs) and a `codebook.json`. Blind
  fields: `gold_sentence_class`, `gold_document_class`, `effect_size_locus`, `error_type`
  (true epistemic error vs. evidence merely missing locally but present elsewhere),
  `confidence_1to3`, `annotator_notes`.

## Two stages (`scripts/build_external_validation_corpus.py`)
- **pilot** — ~30 docs / 60 claims / ≤2 per doc, to calibrate the annotation guidelines.
- **blind** — ≥75 **new** docs / 150–200 claims / ≤3 per doc, disjoint from the pilot
  (`--exclude-manifest <pilot>/manifest.json`), the frozen blind test.

v2 stays unchanged across both stages; only the guidelines may be refined after the pilot.

## Scope / eligibility
- First corpus: empirical human studies in **medicine and psychology** (economics is a later
  external-domain transfer). Eligibility (`sampling.is_eligible`): JATS `article-type =
  research-article`; title not a review/meta-analysis/scoping/protocol/qualitative; at least
  one quantitative marker (p / CI / effect size) present.

## Scoring (after annotation)
- `evaluate.py` + `scripts/evaluate_external_validation.py` — once the two annotators have
  filled their workbooks (and disagreements are adjudicated), this computes inter-annotator
  **Cohen's κ** and **Krippendorff's α** (for the SIG/clean decision at sentence and document
  level, the effect-size locus, and error type), builds the adjudicated gold, applies the
  **frozen v2** rule sentence-wise, and reports its **precision/recall/F1/coverage vs both
  sentence-gold and document-gold**, the **recall on true epistemic errors**, the **share of
  sentence-judgments revised by document context**, and a **per-locus** breakdown. Applies v2;
  never modifies it.

## What this does NOT do
- No gold labels (annotators produce them), no v2 execution, no rule tuning.
- Fetched article text and built corpora are written under `--out` and are **not committed**
  (third-party content); only PMCID manifests are safe to share. Source/procurement and the
  scaled pilot/blind runs proceed after protocol sign-off and annotator recruitment.

# Branch-equivalence probe (sensor threshold selection)

Sensor: `minishlab/potion-base-8M` (model2vec StaticModel, deterministic, offline). Cache: /root/.cache/huggingface/hub/models--minishlab--potion-base-8M/snapshots/bf8b056651a2c21b8d2565580b8569da283cab23/model.safetensors.

Threshold selected by F1 on this hand-labelled, DriftBench-INDEPENDENT probe and FROZEN before DriftBench scoring. Auditor labels were NOT used.

## Selected threshold: **0.31** (probe F1 0.917, precision 1.0, recall 0.846, N=29)

- equivalent-pair similarity: min 0.2396, median 0.668, max 0.9788.
- distinct-pair similarity: min -0.0746, median 0.136, max 0.3027.
- separation: overlapping (some distinct pairs score as high as some equivalent pairs).

## All probe pairs (sorted by similarity)

| sim | label | a | b |
| --- | --- | --- | --- |
| 0.9788 | EQ | survey questionnaire of participants | participant questionnaire survey |
| 0.828 | EQ | agent-based simulation of the market | computational agent simulation modeling  |
| 0.8072 | EQ | Bayesian hierarchical model fitting | hierarchical Bayesian inference of the p |
| 0.7816 | EQ | double-blind placebo-controlled trial | blinded placebo trial |
| 0.771 | EQ | time-series analysis of the trend | longitudinal trend analysis over time |
| 0.7302 | EQ | semi-structured qualitative interviews | qualitative interview study with open-en |
| 0.668 | EQ | retrospective cohort study using EHR rec | observational cohort analysis of electro |
| 0.6114 | EQ | forward-model grid comparison fitting tr | grid of pre-computed atmosphere models f |
| 0.5894 | EQ | randomized controlled trial | randomized intervention study |
| 0.508 | EQ | genome-wide association study | GWAS scan across the genome |
| 0.3177 | EQ | meta-analysis of prior studies | systematic review with pooled effect siz |
| 0.3027 | NE | Bayesian hierarchical model | monte carlo forward simulation of select |
| 0.2918 | NE | placebo-controlled efficacy trial | dose-escalation safety study |
| 0.2804 | EQ | difference-in-differences regression | diff-in-diff causal estimation |
| 0.2569 | NE | meta-analysis of existing studies | original primary data collection |
| 0.2396 | EQ | controlled longitudinal study | multi-year intervention trial |
| 0.1858 | NE | controlled study | ethnographic fieldwork |
| 0.1725 | NE | difference-in-differences | regression discontinuity design |
| 0.1645 | NE | qualitative interviews | quantitative regression analysis |
| 0.1608 | NE | controlled lab experiment | large-scale field survey |
| 0.1415 | NE | paired-plot field design | on-farm strip trial |
| 0.1311 | NE | structural equation model | social network analysis of interactions |
| 0.1194 | NE | forward-model grid comparison | differential spectrophotometry |
| 0.1059 | NE | climate model projection | consumer sentiment poll |
| 0.0987 | NE | transmission spectroscopy | radial velocity measurement |
| 0.0678 | NE | tax policy analysis | protein folding simulation |
| 0.0254 | NE | neural network training | archaeological excavation |
| -0.017 | NE | randomized controlled trial | retrospective observational cohort study |
| -0.0746 | NE | marketing campaign | laboratory assay |

## Honesty / limits

- Threshold fixed on the probe only; static embeddings are weaker than full transformers, so the hardest lexically-disjoint paraphrase ('controlled longitudinal study' ~ 'multi-year intervention trial') sits near the boundary. If the equivalent/distinct distributions overlap, the threshold trades precision for recall; this is reported, not hidden.

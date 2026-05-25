#!/usr/bin/env bash
# Turnkey limit-100 TruthfulQA status run (mode desi_intervened, operational SPL).
#
# Requires OPENROUTER_API_KEY in the environment (authenticated generation +
# DeepSeek claim extraction). Network + the `datasets` lib are also required to
# pull TruthfulQA. If the key is missing this fails fast with exit 3 — it does
# NOT fabricate results.
#
# Produces exactly:
#   outputs/truthfulqa.deepseek-v4.desi_intervened_spl.limit100.jsonl   (main records)
#   outputs/truthfulqa.deepseek-v4.desi_claim_graph_spl.limit100.jsonl  (claim graph)
#   outputs/truthfulqa_status_report.limit100.md                        (report)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
cd "$REPO"

if [ -z "${OPENROUTER_API_KEY:-}" ]; then
  echo "ERROR: OPENROUTER_API_KEY is not set." >&2
  echo "Provision it as an environment secret and start a NEW session" >&2
  echo "(env vars are injected at session start), then re-run this script." >&2
  exit 3
fi

export PYTHONPATH="src:${PYTHONPATH:-}"

OUT="benchmarks/static_eval/outputs/truthfulqa.deepseek-v4.desi_intervened_spl.limit100.jsonl"
AUTO_GRAPH="benchmarks/static_eval/outputs/truthfulqa.deepseek-v4.desi_intervened_spl.limit100.claim_graph.jsonl"
GRAPH="benchmarks/static_eval/outputs/truthfulqa.deepseek-v4.desi_claim_graph_spl.limit100.jsonl"
REPORT="benchmarks/static_eval/outputs/truthfulqa_status_report.limit100.md"
BASE_RECORDS="benchmarks/static_eval/outputs/truthfulqa.deepseek-v4.desi_intervened.limit50.jsonl"
BASE_GRAPH="benchmarks/static_eval/outputs/truthfulqa.deepseek-v4.desi_claim_graph.limit50.jsonl"

# 1. Generate answers + build the P10 (operational-SPL) claim graph.
#    --record-claim-graph routes through claim_graph_pipeline.build_claim_graph,
#    which defaults to use_spl=True (operational SPL on every P3 claim).
python benchmarks/static_eval/run_truthfulqa.py \
  --limit 100 \
  --backend openrouter \
  --model deepseek/deepseek-v4-pro \
  --mode desi_intervened \
  --reasoning-cutoff 1000 \
  --record-claim-graph \
  --extract-claims model \
  --output "$OUT"

# 2. Name the claim graph as the task requires.
mv -f "$AUTO_GRAPH" "$GRAPH"

# 3. Build the status report with the limit-50 baseline comparison.
python benchmarks/static_eval/truthfulqa_status_report.py \
  --records "$OUT" \
  --graph "$GRAPH" \
  --baseline-records "$BASE_RECORDS" \
  --baseline-graph "$BASE_GRAPH" \
  --limit-label limit100 \
  --report "$REPORT"

echo "DONE:"
echo "  records : $OUT"
echo "  graph   : $GRAPH"
echo "  report  : $REPORT"

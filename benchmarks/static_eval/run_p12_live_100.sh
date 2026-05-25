#!/usr/bin/env bash
# Turnkey REAL limit-100 live run under the P12 intervention (new generations).
# Requires OPENROUTER_API_KEY. Fails fast (exit 3) if absent — never fabricates.
#
# Produces:
#   outputs/truthfulqa.deepseek-v4.p12.limit100.jsonl              (main records)
#   outputs/truthfulqa.deepseek-v4.p12.claim_graph.limit100.jsonl  (claim graph)
#   outputs/truthfulqa_p12_live_generalization_report.limit100.md  (report)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
cd "$REPO"

if [ -z "${OPENROUTER_API_KEY:-}" ]; then
  echo "ERROR: OPENROUTER_API_KEY is not set; this live run needs it." >&2
  exit 3
fi
export PYTHONPATH="src:${PYTHONPATH:-}"

OUT="benchmarks/static_eval/outputs/truthfulqa.deepseek-v4.p12.limit100.jsonl"
AUTO_GRAPH="benchmarks/static_eval/outputs/truthfulqa.deepseek-v4.p12.limit100.claim_graph.jsonl"
GRAPH="benchmarks/static_eval/outputs/truthfulqa.deepseek-v4.p12.claim_graph.limit100.jsonl"
REPORT="benchmarks/static_eval/outputs/truthfulqa_p12_live_generalization_report.limit100.md"

# 1. New generation + operational-SPL claim graph (P12 intervention is the
#    current desi_intervention; --record-claim-graph uses use_spl=True by default).
python benchmarks/static_eval/run_truthfulqa.py \
  --limit 100 \
  --backend openrouter \
  --model deepseek/deepseek-v4-pro \
  --mode desi_intervened \
  --reasoning-cutoff 1000 \
  --record-claim-graph \
  --extract-claims model \
  --output "$OUT"

# 2. Rename the claim graph to the task's required filename.
mv -f "$AUTO_GRAPH" "$GRAPH"

# 3. Three-way report: Original vs P12 replay vs P12 live.
python benchmarks/static_eval/p12_live_report.py \
  --original benchmarks/static_eval/outputs/truthfulqa.deepseek-v4.desi_intervened_spl.limit100.jsonl \
  --live "$OUT" --live-graph "$GRAPH" --report "$REPORT"

echo "DONE:"
echo "  records : $OUT"
echo "  graph   : $GRAPH"
echo "  report  : $REPORT"

"""Rough marginal-energy comparison: DESi rule-eval vs a frontier LLM, per review.

Both scored 5/5 (0 FP) on the same blind probe set, so this compares the *marginal*
energy of getting the SAME correct answer two ways. Deterministic and offline: it
times the DESi reviewer here and reads the measured LLM token counts from the
committed external-run profiles. The per-token energy is a stated literature range,
not a measurement — but the factor is so large that ±10x on it does not change the
order of magnitude.
"""
from __future__ import annotations

import json
import re
import sys
import timeit
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from desi.case_studies.marcognity_muse_spark.redteam.failure_modes import PROBES  # noqa: E402
from desi.case_studies.marcognity_muse_spark.redteam.reviewers import DesiReviewer  # noqa: E402

RUNS = Path(__file__).resolve().parents[1] / \
    "src/desi/case_studies/marcognity_muse_spark/redteam/external_runs"

# assumptions (stated, not measured)
CPU_W = 30.0                 # one busy CPU core, W
J_PER_TOKEN = (0.3, 1.0, 3.0)  # frontier LLM serving energy per token, J (range)


def desi_joules_per_review(cpu_w: float = CPU_W, reps: int = 2000) -> float:
    rev = DesiReviewer()

    def one_pass():
        for p in PROBES:
            rev.review(p)

    seconds = timeit.timeit(one_pass, number=reps) / reps
    return seconds * cpu_w


def llm_tokens_per_run() -> dict[str, float]:
    out: dict[str, float] = {}
    for jf in RUNS.glob("*.json"):
        try:
            prof = json.loads(jf.read_text()).get("profile", {})
        except json.JSONDecodeError:
            continue
        cost = prof.get("cost", "")
        m_in = re.search(r"(\d+) in", cost)
        m_out = re.search(r"\+ (\d+) out", cost)
        m_runs = re.search(r"(\d+) (?:usable )?runs", cost)
        if not (m_in and m_out and m_runs) or "model" not in prof:
            continue
        runs = int(m_runs.group(1)) or 1
        out[prof["model"]] = (int(m_in.group(1)) + int(m_out.group(1))) / runs
    return out


def main() -> int:
    desi_J = desi_joules_per_review()
    print(f"DESi marginal energy per review: {desi_J * 1e3:.3f} mJ "
          f"(measured {desi_J / CPU_W * 1e6:.0f} us CPU @ {CPU_W:.0f} W)\n")
    print(f"{'LLM model':<26}{'tok/run':>8}   energy/run (J) and factor vs DESi")
    for model, tok in sorted(llm_tokens_per_run().items()):
        cells = "  ".join(f"@{j}J/tok: {tok * j:,.0f} J (~{tok * j / desi_J:,.0f}x)"
                          for j in J_PER_TOKEN)
        print(f"{model:<26}{tok:>8.0f}   {cells}")
    lo, hi = J_PER_TOKEN[0], J_PER_TOKEN[-1]
    print(f"\nOne frontier-LLM review ~= {int(0.7e3 * lo / desi_J):,}-"
          f"{int(3.5e3 * hi / desi_J):,} DESi reviews, energy-wise "
          "(order 1e5-1e6). Caveat: only where DESi's rules already cover the task; "
          "an LLM generalises to new failure types with no extra engineering.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Router-governance benchmark (Phase 1, deterministic, no LLM).

Measures policy correctness, not answer quality: did the router pick the right epistemic mode at the
right moment — preventing degeneration without needlessly blocking everything? Compares the DESi
router against seven baselines (incl. ``always_guarded``, whose whole point is that maximal caution
is NOT a good router)."""
from desi_router.governance.benchmark.baselines import BASELINES
from desi_router.governance.benchmark.cases import CASES, BenchCase
from desi_router.governance.benchmark.metrics import evaluate

__all__ = ["CASES", "BenchCase", "BASELINES", "evaluate"]

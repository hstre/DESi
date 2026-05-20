"""DESi v3.96b - root cause isolation.

Static trace of non-determinism sources inside
``src/desi/``. Classifies each hit by container
kind and suggested fix; surfaces the high-risk
``builtin_hash`` use that produces the
StateVector drift observed in v3.96a.
"""
from __future__ import annotations

from .containers import (
    container_kind_counts,
    high_risk_hit_count,
    total_hit_count,
    unstable_container_kinds,
)
from .ordering import (
    OrderingClassification, OrderingFix,
    all_classifications,
    unstable_functions,
)
from .report import (
    V396bReport,
    build_report,
    build_root_cause_trace_artifact,
)
from .trace import (
    TraceHit, all_trace_hits,
    builtin_hash_hits, hits_by_kind,
    is_high_risk,
)


__all__ = [
    "OrderingClassification", "OrderingFix",
    "TraceHit",
    "V396bReport",
    "all_classifications",
    "all_trace_hits",
    "build_report",
    "build_root_cause_trace_artifact",
    "builtin_hash_hits",
    "container_kind_counts",
    "high_risk_hit_count",
    "hits_by_kind", "is_high_risk",
    "total_hit_count",
    "unstable_container_kinds",
    "unstable_functions",
]

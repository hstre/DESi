"""FrameInvarianceReport — Aufgabe 9."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .metrics import FrameInvarianceMetrics, compute_invariance_metrics
from .runner import FrameInvarianceRun


@dataclass(frozen=True)
class FrameInvarianceReport:
    started_at: datetime
    finished_at: datetime
    metrics: FrameInvarianceMetrics
    negative_control_distinguished: int
    negative_control_total: int
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "metrics": self.metrics.to_dict(),
            "negative_control_distinguished":
                self.negative_control_distinguished,
            "negative_control_total":
                self.negative_control_total,
            "replay_hash": self.replay_hash,
        }


def _replay_hash(payload: dict[str, Any]) -> str:
    cleaned = {k: v for k, v in payload.items()
               if k not in ("started_at", "finished_at", "replay_hash")}
    raw = json.dumps(
        cleaned, sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def build_invariance_report(
    run: FrameInvarianceRun,
    *,
    started_at: datetime,
    finished_at: datetime,
) -> FrameInvarianceReport:
    metrics = compute_invariance_metrics(run)
    nc_distinguished = sum(
        1 for nc in run.negative_controls if nc.distinguished
    )
    payload = {
        "metrics": metrics.to_dict(),
        "negative_control_distinguished": nc_distinguished,
        "negative_control_total": len(run.negative_controls),
    }
    return FrameInvarianceReport(
        started_at=started_at,
        finished_at=finished_at,
        metrics=metrics,
        negative_control_distinguished=nc_distinguished,
        negative_control_total=len(run.negative_controls),
        replay_hash=_replay_hash(payload),
    )


__all__ = ["FrameInvarianceReport", "build_invariance_report"]

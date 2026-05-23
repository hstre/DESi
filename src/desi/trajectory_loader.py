"""JSON trajectory loader with explicit validation errors."""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from .models import Trajectory


class TrajectoryLoadError(ValueError):
    """Raised when a trajectory file is missing, malformed, or invalid."""


_REQUIRED_TOP_LEVEL = ("trajectory_id", "steps")


def load_trajectory(path: str | Path) -> Trajectory:
    """Load and validate a trajectory JSON file.

    Errors are raised as :class:`TrajectoryLoadError` with a message that
    points at the offending file and field.
    """
    p = Path(path)
    if not p.is_file():
        raise TrajectoryLoadError(f"Trajectory file not found: {p}")

    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TrajectoryLoadError(
            f"{p}: invalid JSON at line {exc.lineno} col {exc.colno}: {exc.msg}"
        ) from exc

    if not isinstance(raw, dict):
        raise TrajectoryLoadError(
            f"{p}: top-level JSON must be an object, got {type(raw).__name__}"
        )

    for field in _REQUIRED_TOP_LEVEL:
        if field not in raw:
            raise TrajectoryLoadError(f"{p}: missing required field '{field}'")

    try:
        return Trajectory.model_validate(raw)
    except ValidationError as exc:
        raise TrajectoryLoadError(f"{p}: schema validation failed:\n{exc}") from exc

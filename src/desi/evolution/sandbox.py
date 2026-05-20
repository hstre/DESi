"""CloneSandbox — isolated copy of stable DESi configuration.

The sandbox owns two pieces of state:

* a **frozen** snapshot of stable configuration plus stable memory
* a **mutable** clone that can apply a MutationProposal's config_delta

The contract is one-way: the clone may read stable, but it may not
write to it. Tests in :mod:`tests.evolution.test_sandbox` enforce
this — every mutation of the clone must leave the stable state
byte-identical.

v0.5 keeps the configuration model deliberately simple: a flat dict
of named knobs. The downstream MutationEvaluation reads the clone
configuration to parameterise its evaluation runs.
"""
from __future__ import annotations

import copy
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .proposal import MutationProposal


@dataclass(frozen=True)
class StableConfig:
    """The frozen stable configuration.

    Frozen dataclass + tuple-of-items hash means a stable_id can be
    computed deterministically and compared across runs.
    """

    version: str
    knobs: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    @property
    def as_dict(self) -> dict[str, Any]:
        return dict(self.knobs)

    @property
    def stable_id(self) -> str:
        items = sorted((str(k), str(v)) for k, v in self.knobs)
        raw = "\x00".join(f"{k}={v}" for k, v in items).encode("utf-8")
        return "stable_" + hashlib.sha256(raw).hexdigest()[:12]

    @classmethod
    def from_dict(cls, version: str, knobs: dict[str, Any]) -> "StableConfig":
        return cls(version=version,
                   knobs=tuple(sorted(knobs.items(), key=lambda p: p[0])))


# Default knob set the v0.5 documentation references.
DEFAULT_STABLE_KNOBS: dict[str, Any] = {
    "guard_thresholds.merge_similarity_min": 0.85,
    "guard_thresholds.branch_open_evidence_min": 0.30,
    "branch_heuristics.max_open_branches": 4,
    "merge_policy.require_method_equivalence": True,
    "operator_ordering.commit_after_n_consistent_steps": 3,
    "diagnostics.late_guard_percentile": 0.75,
}


def default_stable() -> StableConfig:
    return StableConfig.from_dict("stable-v0.5.0", DEFAULT_STABLE_KNOBS)


class CloneSandbox:
    """An isolated, mutable clone derived from a :class:`StableConfig`.

    The constructor accepts the stable config + an optional snapshot
    id (e.g. the memory-layer snapshot the clone is built from). The
    sandbox stores the stable config as an immutable reference and
    exposes a *copy* via :attr:`config`. Mutations applied via
    :meth:`apply` modify the copy; they never touch the stable side.
    """

    def __init__(
        self,
        stable: StableConfig,
        *,
        parent_snapshot_id: str | None = None,
        clone_id: str | None = None,
    ) -> None:
        self._stable = stable
        self.clone_id = clone_id or ("clone_" + uuid.uuid4().hex[:12])
        self.parent_snapshot_id = (
            parent_snapshot_id or stable.stable_id
        )
        # Deep-copy in case knob values are non-hashable containers.
        self._clone_knobs: dict[str, Any] = copy.deepcopy(stable.as_dict)
        self._applied_proposals: list[str] = []
        self._created_at: datetime = datetime.now(timezone.utc)
        # Block-list of stable-only operations the clone may not perform.
        self._stable_writes_blocked: bool = True

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    @property
    def stable(self) -> StableConfig:
        """The unchanged stable configuration."""
        return self._stable

    @property
    def config(self) -> dict[str, Any]:
        """A *copy* of the current clone configuration.

        Callers receive a fresh dict so that mutating it externally
        does not bleed into the sandbox. Use :meth:`apply` to modify
        the clone's configuration.
        """
        return copy.deepcopy(self._clone_knobs)

    @property
    def applied_proposals(self) -> tuple[str, ...]:
        return tuple(self._applied_proposals)

    @property
    def created_at(self) -> datetime:
        return self._created_at

    # ------------------------------------------------------------------
    # Writes (clone-only)
    # ------------------------------------------------------------------

    def apply(self, proposal: MutationProposal) -> None:
        """Apply a proposal's config_delta to the clone.

        Stable is untouched. Multiple proposals can be applied in
        sequence; their order is recorded for audit.
        """
        if proposal.parent_version != self._stable.version:
            raise SandboxIsolationError(
                f"proposal {proposal.mutation_id} targets parent_version="
                f"{proposal.parent_version!r}, but this sandbox is built "
                f"from stable version {self._stable.version!r}"
            )
        # Apply config_delta to the clone-side knobs only.
        for k, v in proposal.config_delta.items():
            self._clone_knobs[k] = v
        self._applied_proposals.append(proposal.mutation_id)

    def write_to_stable(self, *_args: Any, **_kwargs: Any) -> None:
        """Explicit guard against accidental stable writes."""
        raise SandboxIsolationError(
            "CloneSandbox is observation-isolated; writes to stable "
            "state are forbidden. Use the Promotion path."
        )

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    def diff(self) -> dict[str, tuple[Any, Any]]:
        """Return a (stable_value, clone_value) tuple per changed knob."""
        out: dict[str, tuple[Any, Any]] = {}
        stable = self._stable.as_dict
        for k, v in self._clone_knobs.items():
            sv = stable.get(k, "<absent>")
            if sv != v:
                out[k] = (sv, v)
        return out


class SandboxIsolationError(RuntimeError):
    """Raised when a caller would have violated the clone-only contract."""

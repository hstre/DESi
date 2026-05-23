"""Impact tracking — which claims depend on which tool versions?

Two helpers per the v1.9 directive:

* :class:`ImpactScan` answers
  *"Which claims depend on tool X version Y?"*

* :class:`ContaminationPropagation` answers
  *"If tool version Y is wrong — which downstream claims are
  contaminated?"*

Both operate over a single in-memory registry that the v1.9 mini-
benchmark populates as it runs. The registry is a frozen-dataclass
record so the contamination scan is replayable: identical inputs
produce identical contamination sets across processes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .provenance import ToolProvenance


@dataclass(frozen=True)
class ToolUsageRecord:
    """One (claim, tool-execution) attribution.

    The same claim id may appear with multiple tool executions
    (e.g. a re-audit) — each appearance is its own record so the
    audit trail keeps every history.
    """

    claim_id: str
    provenance: ToolProvenance


class ToolUsageRegistry:
    """In-memory append-only registry of (claim_id, ToolProvenance) pairs."""

    def __init__(self) -> None:
        self._records: list[ToolUsageRecord] = []

    def record(self, claim_id: str, provenance: ToolProvenance) -> None:
        self._records.append(ToolUsageRecord(
            claim_id=claim_id, provenance=provenance,
        ))

    def all_records(self) -> tuple[ToolUsageRecord, ...]:
        return tuple(self._records)

    def __len__(self) -> int:
        return len(self._records)


@dataclass(frozen=True)
class ImpactScan:
    """Result of an impact scan against a usage registry.

    Lists every claim id whose recorded :class:`ToolProvenance`
    matches the (tool_name, optional tool_version) query.
    """

    tool_name: str
    tool_version: str | None
    claim_ids: tuple[str, ...] = field(default_factory=tuple)
    record_count: int = 0

    def to_dict(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "claim_ids": list(self.claim_ids),
            "record_count": self.record_count,
        }

    @classmethod
    def for_tool(
        cls,
        registry: ToolUsageRegistry,
        *,
        tool_name: str,
        tool_version: str | None = None,
    ) -> "ImpactScan":
        """Compute an :class:`ImpactScan` for ``(tool_name, tool_version)``."""
        hits: list[ToolUsageRecord] = []
        for r in registry.all_records():
            if r.provenance.tool_name != tool_name:
                continue
            if (tool_version is not None
                    and r.provenance.tool_version != tool_version):
                continue
            hits.append(r)
        return cls(
            tool_name=tool_name,
            tool_version=tool_version,
            claim_ids=tuple(sorted({r.claim_id for r in hits})),
            record_count=len(hits),
        )


@dataclass(frozen=True)
class ContaminationPropagation:
    """Result of a contamination scan.

    Asks: if (tool_name, tool_version) turns out to be wrong, which
    claims and downstream claims are contaminated?

    v1.9 ships the *direct* propagation only — every claim with a
    matching :class:`ToolProvenance` is contaminated. A future
    release may extend with chain-propagation (claims whose audit
    proof_chain references a contaminated claim are also
    contaminated). The v1.9 implementation is honest about that:
    ``downstream_claim_ids`` includes only directly-affected ids.
    """

    tool_name: str
    tool_version: str | None
    contaminated_claim_ids: tuple[str, ...] = field(default_factory=tuple)
    downstream_claim_ids: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "contaminated_claim_ids": list(self.contaminated_claim_ids),
            "downstream_claim_ids": list(self.downstream_claim_ids),
        }

    @classmethod
    def for_tool(
        cls,
        registry: ToolUsageRegistry,
        *,
        tool_name: str,
        tool_version: str | None = None,
        downstream_dependencies: dict[str, Iterable[str]] | None = None,
    ) -> "ContaminationPropagation":
        """Compute the contamination set.

        ``downstream_dependencies`` is an optional ``{claim_id: [child_ids]}``
        adjacency — when supplied, every transitively-reachable
        descendant of a contaminated claim is added to
        ``downstream_claim_ids``.
        """
        scan = ImpactScan.for_tool(
            registry, tool_name=tool_name, tool_version=tool_version,
        )
        contaminated = set(scan.claim_ids)
        downstream: set[str] = set()
        if downstream_dependencies:
            stack = list(contaminated)
            seen = set(contaminated)
            while stack:
                cid = stack.pop()
                for child in downstream_dependencies.get(cid, ()):
                    if child in seen:
                        continue
                    seen.add(child)
                    downstream.add(child)
                    stack.append(child)
        return cls(
            tool_name=tool_name,
            tool_version=tool_version,
            contaminated_claim_ids=tuple(sorted(contaminated)),
            downstream_claim_ids=tuple(sorted(downstream)),
        )


__all__ = [
    "ContaminationPropagation",
    "ImpactScan",
    "ToolUsageRecord",
    "ToolUsageRegistry",
]

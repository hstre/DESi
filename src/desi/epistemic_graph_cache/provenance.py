"""v24.2 - epistemic subspace provenance.

A reusable epistemic subspace is the neighbourhood of a claim:
its replay hashes, fixtures, governance rules, the claim itself
and the metrics that support it. The subspace fingerprint is a
deterministic hash over exactly these five components - the five
identity conditions the cache rule depends on. Any change to any
component changes the fingerprint.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from desi.epistemic_graph import edges_of_type, nodes_of_type, out_edges
from desi.epistemic_graph.nodes import NodeType

# the five identity components, in canonical order
COMPONENTS: tuple[str, ...] = (
    "replay_hashes", "fixtures", "governance", "claims",
    "metrics",
)


def _replay_hash_values() -> dict[str, str]:
    return {
        n.node_id: n.label
        for n in nodes_of_type(NodeType.REPLAY_HASH.value)
    }


@dataclass(frozen=True)
class Subspace:
    subspace_id: str
    replay_hashes: tuple[str, ...]
    fixtures: tuple[str, ...]
    governance: tuple[str, ...]
    claims: tuple[str, ...]
    metrics: tuple[str, ...]

    def component(self, name: str) -> tuple[str, ...]:
        return getattr(self, name)

    def fingerprint(self) -> str:
        parts = []
        for comp in COMPONENTS:
            vals = sorted(self.component(comp))
            parts.append(f"{comp}=" + ",".join(vals))
        return hashlib.sha256(
            "|".join(parts).encode("utf-8"),
        ).hexdigest()

    def perturbed(self, component: str) -> "Subspace":
        """Return a copy with one component changed, modelling a
        change in that identity condition (for stale tests)."""
        if component not in COMPONENTS:
            raise KeyError(component)
        changed = tuple(
            sorted(self.component(component) + ("__changed__",))
        )
        kw = {c: self.component(c) for c in COMPONENTS}
        kw[component] = changed
        return Subspace(self.subspace_id, **kw)

    def to_dict(self) -> dict[str, object]:
        return {
            "subspace_id": self.subspace_id,
            "replay_hashes": list(self.replay_hashes),
            "fixtures": list(self.fixtures),
            "governance": list(self.governance),
            "claims": list(self.claims),
            "metrics": list(self.metrics),
            "fingerprint": self.fingerprint(),
        }


def _supporting_metrics(claim_node_id: str) -> tuple[str, ...]:
    return tuple(sorted(
        e.source for e in edges_of_type("SUPPORTS")
        if e.target == claim_node_id
    ))


def subspaces() -> tuple[Subspace, ...]:
    rh_values = _replay_hash_values()
    result: list[Subspace] = []
    for claim in nodes_of_type(NodeType.CLAIM.value):
        cid = claim.node_id
        out = out_edges(cid)
        fixtures = tuple(sorted(
            e.target for e in out
            if e.edge_type == "DERIVED_FROM"
            and e.target.startswith("fixture:")
        ))
        governance = tuple(sorted(
            e.target for e in out if e.edge_type == "GOVERNED_BY"
        ))
        replay_hashes = tuple(sorted(
            rh_values.get(e.target, e.target)
            for e in out if e.edge_type == "VALIDATED_BY"
            and e.target.startswith("replayhash:")
        ))
        metrics = _supporting_metrics(cid)
        result.append(Subspace(
            subspace_id=cid.split(":", 1)[1],
            replay_hashes=replay_hashes,
            fixtures=fixtures,
            governance=governance,
            claims=(cid,),
            metrics=metrics,
        ))
    return tuple(
        sorted(result, key=lambda s: s.subspace_id)
    )


def current_fingerprints() -> dict[str, str]:
    return {s.subspace_id: s.fingerprint() for s in subspaces()}


__all__ = [
    "COMPONENTS",
    "Subspace",
    "current_fingerprints",
    "subspaces",
]

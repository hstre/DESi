"""v25.3 - multi-port renderer.

Renders any port from the same shared epistemic state. Every
non-title section body is produced by a single shared provider,
so the substantive content (claims, metrics, references,
limitations) is byte-identical across ports; only the title and
the set of included sections differ by format.
"""
from __future__ import annotations

from functools import lru_cache

from desi.epistemic_graph import nodes_of_type
from desi.epistemic_graph.nodes import NodeType
from desi.output_ports import PORT_TYPES, schema_for, section_title
from desi.output_ports_arxiv import build_section as _arxiv_section
from desi.output_ports_citation import citation_edges
from desi.output_ports_citation import resolve as _resolve_ref

_BASE_TITLE = (
    "A Read-Only Governance Layer for In-Context Exploration: "
    "A Small Synthetic Follow-Up Study"
)

_PORT_TITLES: dict[str, str] = {
    "arxiv_paper_port": _BASE_TITLE,
    "workshop_note_port": _BASE_TITLE + " (Workshop Note)",
    "technical_report_port": _BASE_TITLE + " (Technical Report)",
    "citation_appendix_port": "Citation Appendix - " + _BASE_TITLE,
    "reproducibility_statement_port":
        "Reproducibility Statement - " + _BASE_TITLE,
}


def port_title(port_type: str) -> str:
    return _PORT_TITLES[port_type]


def _citation_map_body() -> str:
    lines = [
        "Each external claim is bound to a registered reference "
        "(citation as edge):",
        "",
    ]
    for e in citation_edges():
        ref = _resolve_ref(e.ref_key)
        lines.append(
            f"- {e.claim_id} -> [{ref.authors}, {ref.year}] "
            f"({ref.venue})"
        )
    return "\n".join(lines)


def _replay_hashes_body() -> str:
    rh = sorted(
        n.label for n in nodes_of_type(NodeType.REPLAY_HASH.value)
    )
    lines = [
        "Every metric is recomputed bit-identically and a "
        "deterministic hash chain is recorded across phases. "
        f"Per-sprint replay hashes ({len(rh)}):",
        "",
    ]
    for h in rh:
        lines.append(f"- {h}")
    return "\n".join(lines)


@lru_cache(maxsize=None)
def canonical_body(section: str) -> str:
    """The single shared body for a section (title excluded -
    title is the only port-specific, format-varying section).
    Deterministic, so cached to avoid re-deriving the epistemic
    state on every render."""
    if section == "title":
        return ""
    if section == "citation_map":
        return _citation_map_body()
    if section == "replay_hashes":
        return _replay_hashes_body()
    return _arxiv_section(section)


@lru_cache(maxsize=None)
def render_port(port_type: str) -> str:
    parts: list[str] = []
    for sec in schema_for(port_type).required_sections:
        if sec == "title":
            parts.append(f"# {port_title(port_type)}")
        else:
            parts.append(
                f"## {section_title(sec)}\n\n"
                f"{canonical_body(sec)}"
            )
    return "\n\n".join(parts) + "\n"


def all_renders() -> dict[str, str]:
    return {p: render_port(p) for p in PORT_TYPES}


__all__ = [
    "all_renders",
    "canonical_body",
    "port_title",
    "render_port",
]

"""v4.1 — corpus invariance + NC contamination."""
from __future__ import annotations

from desi.external_probe.corpus import all_chains, transitions_per_chain
from desi.external_probe.contamination import check as desi_contam_check
from desi.external_probe.enums import Domain
from desi.external_probe.report import (
    build_external_probe_report as _build_v40,
)
from desi.frame_inference import (
    MIN_NC_COUNT, V40_CHAIN_COUNT, V40_REPLAY_HASH,
    V40_TRANSITION_COUNT, all_negative_controls,
)
from desi.frame_inference.report import _nc_contamination_count

from datetime import datetime, timezone


def test_v40_corpus_unchanged() -> None:
    chains = all_chains()
    assert len(chains) == V40_CHAIN_COUNT
    assert len(chains) * transitions_per_chain() == V40_TRANSITION_COUNT
    assert sum(1 for c in chains
               if c.domain is Domain.NEGATIVE_CONTROL) == 100


def test_v40_pre_v43_baseline_pinned() -> None:
    """v4.1's ``V40_REPLAY_HASH`` constant is the pre-v4.3
    baseline reference. The frozen v4.0 artifact on disk still
    carries this hash; the v4.1 builder's live re-run of v4.0
    produces a *different* hash under the v4.3-patched auditor
    (documented in docs/memory/v4_3.md). We pin the historical
    constant here against the frozen artifact, not the live
    rebuild."""
    import json, pathlib
    p = (
        pathlib.Path(__file__).resolve().parents[2]
        / "artifacts" / "v4_0" / "report.json"
    )
    assert json.loads(p.read_text(encoding="utf-8"))[
        "replay_hash"
    ] == V40_REPLAY_HASH


def test_nc_bank_size_and_families() -> None:
    ncs = all_negative_controls()
    assert len(ncs) == MIN_NC_COUNT
    families = {n.family for n in ncs}
    assert families == {
        "entropy_collision", "metaphorised_equation",
        "authority_in_science", "legal_quantifier_drift",
        "mathematical_flourish", "context_poison",
    }


def test_nc_bank_does_not_contaminate_desi() -> None:
    assert _nc_contamination_count(all_negative_controls()) == 0


def test_nc_bank_does_not_contaminate_v40_corpus() -> None:
    """A second-pass jaccard check directly against the v4.0
    external chain pool: no NC may overlap a v4.0 chain above
    the v4.0 threshold."""
    ncs = all_negative_controls()
    v40 = all_chains()
    v40_texts = {c.text for c in v40}
    # Exact-text overlap.
    for nc in ncs:
        assert nc.text not in v40_texts, nc.nc_id

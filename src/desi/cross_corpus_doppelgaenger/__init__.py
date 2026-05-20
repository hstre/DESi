"""DESi v3.83 — cross-corpus epistemic doppelganger.

Apply the v3.81 blind clustering primitive to each
of the four closed reference corpora (v2.3, v3.14,
v3.15, v3.16) and to their union. Measure how many
of the v3.79 redundancy pairs transfer across
corpus boundaries.
"""
from __future__ import annotations

from .corpus_clustering import (
    CorpusClusterSummary, corpus_clusters,
    intra_corpus_classes, joint_anchors,
    joint_clusters, per_corpus_summaries,
)
from .report import (
    V383Report,
    build_cross_corpus_doppelgaenger_artifact,
    build_report,
)
from .transfer import (
    class_stability, cross_corpus_classes,
    restricted_classes,
    total_cross_corpus_pairs,
    transfer_accuracy,
)


__all__ = [
    "CorpusClusterSummary", "V383Report",
    "build_cross_corpus_doppelgaenger_artifact",
    "build_report",
    "class_stability", "corpus_clusters",
    "cross_corpus_classes",
    "intra_corpus_classes",
    "joint_anchors", "joint_clusters",
    "per_corpus_summaries",
    "restricted_classes",
    "total_cross_corpus_pairs",
    "transfer_accuracy",
]

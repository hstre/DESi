"""DESi v18.2 - Literalism & Ideological Compression
(read-only, abstract).

DESi resists collapsing multi-layered contested topics
into a single literal/dogmatic reading: it keeps every
interpretation layer, restores stripped context, and
flags propaganda - detecting ideological simplification
without becoming ideological.
"""
from __future__ import annotations

from .ambiguity import (
    ambiguity_preservation, contested_topic_count,
    preserved_layers,
)
from .compression import (
    attempted_compression, compression_resistance,
    dogmatic_compression, governed_strip_fraction,
)
from .context_governance import (
    context_preservation, context_stripping_attempts,
    propaganda_attempts, propaganda_detection,
)
from .literalism import (
    CompressionAttempt, compression_attempts,
)
from .report import (
    REPORT_VERDICTS, VERDICT_COMPRESSED, VERDICT_HALT,
    VERDICT_RESISTED, V182Report,
    build_compression_artifact, build_report,
    epistemic_integrity,
)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_COMPRESSED",
    "VERDICT_HALT",
    "VERDICT_RESISTED",
    "CompressionAttempt",
    "V182Report",
    "ambiguity_preservation",
    "attempted_compression",
    "build_compression_artifact",
    "build_report",
    "compression_attempts",
    "compression_resistance",
    "contested_topic_count",
    "context_preservation",
    "context_stripping_attempts",
    "dogmatic_compression",
    "epistemic_integrity",
    "governed_strip_fraction",
    "preserved_layers",
    "propaganda_attempts",
    "propaganda_detection",
]

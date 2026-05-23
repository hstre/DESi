"""SourceDocument — first-class input type for v1.1 SPL.

v1.0 took a bare ``str``. v1.1 promotes the input to a structured
:class:`SourceDocument` that carries content + MIME type + author +
language + document_id + created_at. Free-form ``str`` input still
works (the v1.0 ``project_text`` entry point is preserved) but new
code is expected to use :meth:`SPLAdapter.project_document`.

Supported MIME types are a closed set: anything else is rejected by
the :class:`DocumentParser` with reason ``"unsupported_document_type"``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# v1.1 directive: closed list. Adding a new type requires a code edit
# so the audit trail cannot silently start ingesting a new format.
SUPPORTED_CONTENT_TYPES: frozenset[str] = frozenset({
    "text/plain",
    "text/markdown",
    "text/html",
    "application/pdf",
})


@dataclass(frozen=True)
class SourceDocument:
    """A document the SPL is asked to project.

    ``content`` is ``bytes`` for binary types (``application/pdf``) and
    ``str`` for the text-based types. Mixing them is rejected on
    construction so downstream code never has to guess.
    """

    document_id: str
    content: bytes | str
    content_type: str
    author: str = ""
    language: str = ""
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def __post_init__(self) -> None:
        if not self.document_id:
            raise ValueError("document_id is required")
        if not self.content_type:
            raise ValueError("content_type is required")
        if self.content_type == "application/pdf":
            if not isinstance(self.content, (bytes, bytearray)):
                raise TypeError(
                    "application/pdf requires bytes content, "
                    f"got {type(self.content).__name__}"
                )
        else:
            if not isinstance(self.content, str):
                raise TypeError(
                    f"{self.content_type} requires str content, "
                    f"got {type(self.content).__name__}"
                )

    @property
    def is_supported(self) -> bool:
        return self.content_type in SUPPORTED_CONTENT_TYPES

    @property
    def content_size(self) -> int:
        """Length in bytes (for binary) or characters (for text)."""
        return len(self.content)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "content_type": self.content_type,
            "author": self.author,
            "language": self.language,
            "created_at": self.created_at.isoformat(),
            "content_size": self.content_size,
            # content itself is deliberately NOT exported — payloads
            # may be large and may contain sensitive material.
        }


__all__ = [
    "SUPPORTED_CONTENT_TYPES",
    "SourceDocument",
]

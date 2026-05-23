"""desi.install_usability - dummy-friendly install readiness check."""
from __future__ import annotations

from .report import (
    assessment, build_go_no_go, config_loader_works,
    dummy_install_path_works, install_docs_created, is_go,
    offline_default_preserved, secrets_protected,
)

__all__ = [
    "assessment",
    "build_go_no_go",
    "config_loader_works",
    "dummy_install_path_works",
    "install_docs_created",
    "is_go",
    "offline_default_preserved",
    "secrets_protected",
]

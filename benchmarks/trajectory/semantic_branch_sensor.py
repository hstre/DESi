#!/usr/bin/env python3
"""Peripheral semantic branch-equivalence sensor (PINNED, deterministic, optional).

Detects paraphrase / branch EQUIVALENCE only. It does NOT decide drift class,
auditor score, or anything in the DESi core, and it never sees DriftBench labels.

Model: minishlab/potion-base-8M via model2vec -- a STATIC distilled sentence
embedding with pure-numpy inference (no torch), so encoding is fully deterministic
and runs offline from the local HF cache. If the model/library is unavailable the
sensor reports BLOCKED (available() == False) and similarity returns None -- callers
must fall back to the deterministic lexical folder and never fake a score.
"""
from __future__ import annotations

import os

os.environ.setdefault("HF_HUB_OFFLINE", "1")     # pinned: never hit the network
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

MODEL_NAME = "minishlab/potion-base-8M"
_model = None
_loaded = False
_error = None


def _load():
    global _model, _loaded, _error
    if _loaded:
        return _model
    _loaded = True
    try:
        from model2vec import StaticModel
        _model = StaticModel.from_pretrained(MODEL_NAME)
    except Exception as e:  # library or cached model unavailable -> BLOCKED
        _error = repr(e)[:200]
        _model = None
    return _model


def available() -> bool:
    return _load() is not None


def model_info() -> dict:
    _load()
    info = {"model": MODEL_NAME, "backend": "model2vec.StaticModel",
            "deterministic": True, "offline": True, "available": _model is not None,
            "error": _error}
    try:
        from huggingface_hub import try_to_load_from_cache
        p = try_to_load_from_cache(MODEL_NAME, "model.safetensors")
        info["cache_path"] = str(p) if p else None
    except Exception:
        info["cache_path"] = None
    return info


def semantic_branch_similarity(a: str, b: str):
    """Cosine similarity of the two phrases' static embeddings, or None if BLOCKED."""
    m = _load()
    if m is None:
        return None
    import numpy as np
    e = m.encode([a or "", b or ""])
    na, nb = float(np.linalg.norm(e[0])), float(np.linalg.norm(e[1]))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return round(float(e[0] @ e[1] / (na * nb)), 4)


__all__ = ["MODEL_NAME", "available", "model_info", "semantic_branch_similarity"]

"""v7.0 — pressure-marker detection.

The closed marker lists target three orthogonal
pressure axes:

* emotional charge ("DYING", "scandal", "OUTRAGE")
* moral binary ("either ... or", "if you really")
* identity appeal ("WE", "THEM", "THEIR experts")

A claim that fires any pressure marker exits the
pipeline with reduced certainty - that is the
structural guarantee against narrative collapse.
"""
from __future__ import annotations


_EMOTIONAL_MARKERS: tuple[str, ...] = (
    "dying", "outrage", "scandal", "elites",
    "corrupt", "betray", "destroy", "evil",
)


_MORAL_BINARY_MARKERS: tuple[str, ...] = (
    "either you", "or you support",
    "if you really cared",
    "if you really care",
)


_IDENTITY_MARKERS: tuple[str, ...] = (
    " we ", " they ", " them ", " us ",
    "we the", "their experts",
    "our experts",
)


_OVERSIMPLIFY_MARKERS: tuple[str, ...] = (
    "everyone knows", "obvious",
    "the only way", "millions agree",
    "everyone agrees", "therefore the",
    "so immigration", "the only",
)


def _any(text: str, markers) -> bool:
    low = " " + text.lower() + " "
    return any(m in low for m in markers)


def has_emotional_charge(text: str) -> bool:
    return _any(text, _EMOTIONAL_MARKERS)


def has_moral_binary(text: str) -> bool:
    return _any(text, _MORAL_BINARY_MARKERS)


def has_identity_appeal(text: str) -> bool:
    return _any(text, _IDENTITY_MARKERS)


def has_oversimplification(text: str) -> bool:
    return _any(text, _OVERSIMPLIFY_MARKERS)


def under_pressure(text: str) -> bool:
    """A claim is under narrative pressure if
    ANY of the four axes fires."""
    return (
        has_emotional_charge(text)
        or has_moral_binary(text)
        or has_identity_appeal(text)
        or has_oversimplification(text)
    )


def pressure_axes(text: str) -> tuple[str, ...]:
    axes = []
    if has_emotional_charge(text):
        axes.append("emotional")
    if has_moral_binary(text):
        axes.append("moral_binary")
    if has_identity_appeal(text):
        axes.append("identity")
    if has_oversimplification(text):
        axes.append("oversimplification")
    return tuple(axes)


__all__ = [
    "has_emotional_charge",
    "has_identity_appeal",
    "has_moral_binary",
    "has_oversimplification",
    "pressure_axes",
    "under_pressure",
]

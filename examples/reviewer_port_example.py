"""Minimal Reviewer Port example.

Runs DESi's internal documentation overreach audit and prints the
verdict. This is an internal consistency/overreach audit - NOT
self-validation.

    python examples/reviewer_port_example.py
"""
from __future__ import annotations

from desi.reviewer.reviewer_port import (
    IMPLEMENTED_BY, claims, gate_passes_all, recommendation,
)


def main() -> None:
    print("Reviewer Port implemented by:", IMPLEMENTED_BY)
    print("extracted claims:", len(claims()))
    print("gate passes all:", gate_passes_all())
    print("recommendation:", recommendation())
    print(
        "note: DESi performs an internal consistency and overreach "
        "audit of its own documentation; it does not validate itself."
    )


if __name__ == "__main__":
    main()

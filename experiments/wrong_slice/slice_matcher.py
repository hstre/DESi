"""Standalone strict slice matcher for the wrong-slice ablation.

Drop-in, **stdlib only** — copy this single file into a live experiment harness.
It enforces the load-bearing control of the wrong-slice ablation
(see ``PREREGISTRATION.md``): a candidate "wrong" slice may enter the experiment
only if it is byte-for-byte comparable to the correct slice on everything
*except* its content / pass assignment. Otherwise the ablation silently measures
length, density, or format instead of slice correctness.

Required criteria (all must hold for an admissible wrong slice):

  * equal token length (within tolerance; pass your real tokenizer)
  * equal number of claims
  * equal status-field schema   (identical multiset of status keys)
  * equal provenance-field schema (identical multiset of provenance keys)
  * equal structure / outline   (same Gliederung: outline order, per-claim
    section sequence, and ordered per-claim field schema)
  * equal format                (same format tag)
  * actually different          (content hash differs from the correct slice)

The matcher does NOT judge plausibility (neutral-irrelevant vs
plausible-but-unpassend) — that is a construction property recorded by the
slice constructor, not something checkable here.

No third-party dependencies. ``content_hash`` uses SHA-256 over a canonical
JSON; swap in ``desi.core.replay_kernel.replay_hash`` if you want byte-identity
with the rest of DESi.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Callable

_WORD = re.compile(r"\S+")


def default_token_count(text: str) -> int:
    """Whitespace token count. Replace with your harness's real tokenizer."""
    return len(_WORD.findall(text))


@dataclass
class Claim:
    """One claim in a slice.

    ``status`` and ``provenance`` are field dicts; the matcher compares their
    *keys* (schema), never requiring the values to match. ``section`` is the
    outline section the claim belongs to (part of the structural check).
    """

    text: str
    status: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)
    section: str = ""


@dataclass
class Slice:
    """A slice of epistemic state fed to the model for one pass.

    ``outline`` is the ordered list of section identifiers (the slice's
    Gliederung); ``fmt`` is the serialization format tag.
    """

    claims: list[Claim] = field(default_factory=list)
    pass_id: str = ""
    fmt: str = "desi.slice.v1"
    outline: list[str] = field(default_factory=list)


def render_slice(s: Slice) -> str:
    """Deterministic textual rendering used for token counting.

    Mirrors a serialized slice (claim text + status + provenance + section +
    outline), so token length reflects what the model actually receives.
    Override by passing your own ``render`` to :func:`match` if your harness
    serializes differently.
    """
    return json.dumps(
        {
            "fmt": s.fmt,
            "pass_id": s.pass_id,
            "outline": s.outline,
            "claims": [
                {
                    "text": c.text,
                    "status": c.status,
                    "provenance": c.provenance,
                    "section": c.section,
                }
                for c in s.claims
            ],
        },
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _structure_fingerprint(s: Slice) -> tuple:
    """Arrangement (Gliederung), independent of content and field *values*.

    Captures the outline order, each claim's section in order, and the ordered
    sequence of per-claim field schemas. Two slices with the same fingerprint
    are structurally identical even if every claim's text and field values
    differ.
    """
    return (
        tuple(s.outline),
        tuple(c.section for c in s.claims),
        tuple(
            (tuple(sorted(c.status.keys())), tuple(sorted(c.provenance.keys())))
            for c in s.claims
        ),
    )


def content_hash_text(text: str) -> str:
    """SHA-256 over an arbitrary string (for hashing frozen artifacts)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def content_hash(s: Slice) -> str:
    """SHA-256 over a canonical JSON of the slice content."""
    return content_hash_text(render_slice(s))


def _status_key_multiset(s: Slice) -> Counter:
    c: Counter = Counter()
    for claim in s.claims:
        c.update(claim.status.keys())
    return c


def _provenance_key_multiset(s: Slice) -> Counter:
    c: Counter = Counter()
    for claim in s.claims:
        c.update(claim.provenance.keys())
    return c


@dataclass
class Criterion:
    name: str
    ok: bool
    detail: str


@dataclass
class MatchReport:
    """Result of matching a candidate slice against the correct slice."""

    ok: bool
    criteria: list[Criterion]

    def failed(self) -> list[Criterion]:
        return [c for c in self.criteria if not c.ok]

    def __str__(self) -> str:  # human-readable summary
        head = "ADMISSIBLE" if self.ok else "REJECTED"
        lines = [f"[{head}] wrong-slice match report"]
        for c in self.criteria:
            mark = "ok " if c.ok else "FAIL"
            lines.append(f"  {mark} {c.name}: {c.detail}")
        return "\n".join(lines)


def match(
    correct: Slice,
    candidate: Slice,
    *,
    token_count: Callable[[str], int] = default_token_count,
    token_tolerance: int = 0,
    render: Callable[[Slice], str] = render_slice,
    require_actually_different: bool = True,
) -> MatchReport:
    """Check whether ``candidate`` is an admissible matched wrong slice.

    Pass your harness's real tokenizer as ``token_count`` and the serializer you
    actually feed the model as ``render``. ``token_tolerance`` allows a small
    absolute difference in token length (0 = exact).
    """
    crit: list[Criterion] = []

    # 1. token length
    tc_correct = token_count(render(correct))
    tc_cand = token_count(render(candidate))
    delta = abs(tc_correct - tc_cand)
    crit.append(
        Criterion(
            "token_length",
            delta <= token_tolerance,
            f"correct={tc_correct} candidate={tc_cand} delta={delta} tol={token_tolerance}",
        )
    )

    # 2. claim count
    n_correct, n_cand = len(correct.claims), len(candidate.claims)
    crit.append(
        Criterion(
            "claim_count",
            n_correct == n_cand,
            f"correct={n_correct} candidate={n_cand}",
        )
    )

    # 3. status-field schema (multiset of keys)
    s_correct = _status_key_multiset(correct)
    s_cand = _status_key_multiset(candidate)
    crit.append(
        Criterion(
            "status_field_schema",
            s_correct == s_cand,
            f"correct={dict(s_correct)} candidate={dict(s_cand)}",
        )
    )

    # 4. provenance-field schema (multiset of keys)
    p_correct = _provenance_key_multiset(correct)
    p_cand = _provenance_key_multiset(candidate)
    crit.append(
        Criterion(
            "provenance_field_schema",
            p_correct == p_cand,
            f"correct={dict(p_correct)} candidate={dict(p_cand)}",
        )
    )

    # 5. structure / outline (Gliederung)
    f_correct = _structure_fingerprint(correct)
    f_cand = _structure_fingerprint(candidate)
    crit.append(
        Criterion(
            "structure_outline",
            f_correct == f_cand,
            f"correct={f_correct} candidate={f_cand}",
        )
    )

    # 6. format tag
    crit.append(
        Criterion(
            "format",
            correct.fmt == candidate.fmt,
            f"correct={correct.fmt!r} candidate={candidate.fmt!r}",
        )
    )

    # 7. actually different content
    if require_actually_different:
        h_correct = content_hash(correct)
        h_cand = content_hash(candidate)
        crit.append(
            Criterion(
                "actually_different",
                h_correct != h_cand,
                f"correct={h_correct[:12]} candidate={h_cand[:12]}",
            )
        )

    return MatchReport(ok=all(c.ok for c in crit), criteria=crit)


def is_admissible_wrong_slice(correct: Slice, candidate: Slice, **kwargs) -> bool:
    """Convenience boolean wrapper around :func:`match`."""
    return match(correct, candidate, **kwargs).ok

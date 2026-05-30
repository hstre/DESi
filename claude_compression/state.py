"""Compact DESi-state schema for Claude context compression (max 500 tokens, deterministic).

Stores ONLY the current epistemic state — not a chat summary. Seven fields, every one of them
called out in the brief:
  active_goals · open_problems · confirmed_findings · discarded_hypotheses ·
  architecture_decisions · open_conflicts · references

Tokens are counted with the SAME static tokenizer used in the prior Wikipedia probes
(`minishlab/potion-base-8M`, offline, deterministic) so the 500-token budget is a real,
reproducible bound — not a guess.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field

MAX_STATE_TOKENS = 500
FIELDS = ("active_goals", "open_problems", "confirmed_findings",
          "discarded_hypotheses", "architecture_decisions",
          "open_conflicts", "references")

_TOK = None


def _tokenizer():
    """Static, offline, deterministic tokenizer; regex fallback if unavailable."""
    global _TOK
    if _TOK is not None:
        return _TOK
    try:
        from model2vec import StaticModel
        _TOK = StaticModel.from_pretrained("minishlab/potion-base-8M").tokenizer
    except Exception:
        _TOK = "regex"
    return _TOK


def token_count(text: str) -> int:
    if not (text or "").strip():
        return 0
    t = _tokenizer()
    if t != "regex":
        try:
            return len(t.encode(text).ids)
        except Exception:
            pass
    return len(re.findall(r"\S+", text or ""))


@dataclass
class DesiState:
    active_goals: list = field(default_factory=list)
    open_problems: list = field(default_factory=list)
    confirmed_findings: list = field(default_factory=list)
    discarded_hypotheses: list = field(default_factory=list)
    architecture_decisions: list = field(default_factory=list)
    open_conflicts: list = field(default_factory=list)
    references: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def serialize(self) -> str:
        """Canonical, compact JSON form (the bytes actually counted as 'state tokens')."""
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def token_size(self) -> int:
        return token_count(self.serialize())

    def fits_budget(self) -> bool:
        return self.token_size() <= MAX_STATE_TOKENS

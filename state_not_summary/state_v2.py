"""State schema — structured epistemic entries only, no prose, no narrative."""
from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "claude_compression"))
from state import token_count  # noqa: E402  (reuse the deterministic offline tokenizer)

MAX_STATE_TOKENS = 500

EVIDENCE = ("established", "likely", "unclear", "untested")
CLAIM_STATUS = ("active", "tentative", "frozen")
CONFLICT_STATUS = ("open", "stalled", "resolved")
DOMAINS = ("compression", "extraction", "evaluation", "rehydration", "tokenization",
           "architecture", "fixtures", "tests", "general")

# Bodies are CAPPED short (this is structure, not prose). A body that exceeds the cap is
# evidence the extractor is leaking narrative — flagged, not silently allowed.
MAX_BODY_WORDS = 12


@dataclass
class Claim:
    id: str
    body: str
    status: str = "active"     # active | tentative | frozen
    evidence: str = "untested"  # established | likely | unclear | untested

    def __post_init__(self):
        if self.status not in CLAIM_STATUS:
            raise ValueError(f"claim status not in {CLAIM_STATUS}: {self.status}")
        if self.evidence not in EVIDENCE:
            raise ValueError(f"evidence not in {EVIDENCE}: {self.evidence}")


@dataclass
class Constraint:
    id: str
    body: str
    scope: str = "global"


@dataclass
class Conflict:
    id: str
    claim_ids: tuple
    status: str = "open"

    def __post_init__(self):
        if self.status not in CONFLICT_STATUS:
            raise ValueError(f"conflict status not in {CONFLICT_STATUS}: {self.status}")


@dataclass
class Decision:
    id: str
    body: str
    active_since: str = ""
    replaces: str = ""             # optional Decision.id replaced; empty string = none


@dataclass
class DiscardedPath:
    id: str
    body: str
    reason: str = ""               # single sentence — schema-enforced below


@dataclass
class OpenQuestion:
    id: str
    body: str
    blocking: bool = False


@dataclass
class DesiStateV2:
    active_claims: list = field(default_factory=list)
    active_constraints: list = field(default_factory=list)
    open_conflicts: list = field(default_factory=list)
    decisions: list = field(default_factory=list)
    discarded_paths: list = field(default_factory=list)
    open_questions: list = field(default_factory=list)
    evidence_status: dict = field(default_factory=dict)

    # --- forbidden-content checks -------------------------------------------------------
    def validate_no_prose(self) -> list:
        """Return a list of violation strings; empty means schema-clean (no narrative leaked).
        A body is over-long, or contains chat-style markers, or carries multi-sentence prose."""
        violations = []
        chat_markers = ("\nuser:", "\nassistant:", "you said", "i said", "as we discussed",
                        "in the chat", "earlier in this conversation", "the user", "the assistant")

        def _check(label, body):
            wc = len(body.split())
            if wc > MAX_BODY_WORDS:
                violations.append(f"{label}: body over {MAX_BODY_WORDS} words ({wc}) -> prose risk")
            if body.count(". ") >= 2:
                violations.append(f"{label}: body has multi-sentence prose")
            low = body.lower()
            for m in chat_markers:
                if m in low:
                    violations.append(f"{label}: body contains chat marker '{m.strip()}'")

        for c in self.active_claims:        _check(f"claim {c.id}", c.body)
        for r in self.active_constraints:   _check(f"constraint {r.id}", r.body)
        for d in self.decisions:            _check(f"decision {d.id}", d.body)
        for p in self.discarded_paths:
            _check(f"discarded {p.id}", p.body)
            if p.reason.count(". ") >= 1 or len(p.reason.split()) > 16:
                violations.append(f"discarded {p.id}: reason exceeds one sentence")
        for q in self.open_questions:       _check(f"question {q.id}", q.body)
        for dom in self.evidence_status:
            if dom not in DOMAINS:
                violations.append(f"evidence_status: unknown domain '{dom}'")
            if self.evidence_status[dom] not in EVIDENCE:
                violations.append(f"evidence_status[{dom}]: not in {EVIDENCE}")
        return violations

    # --- serialization ------------------------------------------------------------------
    def to_dict(self) -> dict:
        d = asdict(self)
        # tuples in Conflict become lists via asdict; keep as lists for JSON
        for c in d.get("open_conflicts", []):
            c["claim_ids"] = list(c["claim_ids"])
        return d

    def serialize(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def token_size(self) -> int:
        return token_count(self.serialize())

    def fits_budget(self) -> bool:
        return self.token_size() <= MAX_STATE_TOKENS


def parse(serialized: str) -> DesiStateV2:
    """Round-trip helper: read the canonical JSON form back into a DesiStateV2."""
    d = json.loads(serialized)
    state = DesiStateV2(
        active_claims=[Claim(**c) for c in d.get("active_claims", [])],
        active_constraints=[Constraint(**r) for r in d.get("active_constraints", [])],
        open_conflicts=[Conflict(id=c["id"], claim_ids=tuple(c["claim_ids"]),
                                 status=c.get("status", "open")) for c in d.get("open_conflicts", [])],
        decisions=[Decision(**x) for x in d.get("decisions", [])],
        discarded_paths=[DiscardedPath(**x) for x in d.get("discarded_paths", [])],
        open_questions=[OpenQuestion(**x) for x in d.get("open_questions", [])],
        evidence_status=dict(d.get("evidence_status", {})),
    )
    return state

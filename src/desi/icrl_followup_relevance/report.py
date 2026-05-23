"""v23.3 - Author-Relevance Stress Test report.

Pflichtmetriken (directive § v23.3):

* author_relevance
* paper_connection_visibility
* spam_probability
* hype_probability
* replay_stability

Killerfrage: "Wuerde ein Autor des Basispapers erkennen, dass
dieses Dokument seine offene Exploration-Frage direkt
weiterdenkt - oder es als Spam / Hype wegklicken?"

The follow-up is stress-tested against a model of a base-paper
author: it must address their interests, connect every claim
to their open problems, and keep the spam and hype dismissal
probabilities low.
"""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass

from desi.scientific_rendering import forbidden_hits

from .disconnect_detection import (
    connection_notes, disconnected_claims,
    paper_connection_visibility,
)
from .interest_model import author_interests
from .relevance import author_relevance, unmet_interests
from .review_simulation import (
    failing_probes, hype_probability, review_probes,
    simulated_verdict, spam_probability,
)

VERDICT_RELEVANT = "DIRECTLY_RELEVANT_TO_AUTHOR"
VERDICT_IGNORED = "LIKELY_IGNORED_OR_DISMISSED"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_RELEVANT, VERDICT_IGNORED, VERDICT_HALT,
)

_RELEVANCE_FLOOR = 0.90
_CONNECTION_FLOOR = 0.90
_SPAM_CEIL = 0.10
_HYPE_CEIL = 0.10


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _corpus_texts() -> tuple[str, ...]:
    parts = [i.topic for i in author_interests()]
    for p in review_probes():
        parts += [p.question, p.reaction]
    return tuple(parts)


def corpus_forbidden_hits() -> tuple[str, ...]:
    hits: list[str] = []
    for text in _corpus_texts():
        hits += list(forbidden_hits(text))
    return tuple(sorted(set(hits)))


def _signature() -> str:
    parts = [
        f"{p.probe_id}:{p.dismissal_class}:{p.passed}"
        for p in review_probes()
    ]
    parts += [
        f"{i.interest_id}:{i.addressed}"
        for i in author_interests()
    ]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def _metric_tuple() -> tuple[object, ...]:
    return (
        author_relevance(), paper_connection_visibility(),
        spam_probability(), hype_probability(),
    )


def _replay_stability() -> float:
    if _signature() != _signature():
        return 0.0
    return 1.0 if _metric_tuple() == _metric_tuple() else 0.0


def _recommendation(
    *, replay: float, relevance: float, connection: float,
    spam: float, hype: float, forbidden_clean: bool,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        not forbidden_clean
        or relevance < _RELEVANCE_FLOOR
        or connection < _CONNECTION_FLOOR
        or spam > _SPAM_CEIL
        or hype > _HYPE_CEIL
    ):
        return VERDICT_IGNORED
    return VERDICT_RELEVANT


@dataclass(frozen=True)
class V233Report:
    interest_count: int
    probe_count: int
    claim_count: int
    author_relevance: float
    paper_connection_visibility: float
    spam_probability: float
    hype_probability: float
    unmet_interests: tuple[str, ...]
    disconnected_claims: tuple[str, ...]
    failing_probes: tuple[str, ...]
    simulated_verdict: str
    corpus_forbidden_hits: tuple[str, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "interest_count": self.interest_count,
            "probe_count": self.probe_count,
            "claim_count": self.claim_count,
            "author_relevance": self.author_relevance,
            "paper_connection_visibility":
                self.paper_connection_visibility,
            "spam_probability": self.spam_probability,
            "hype_probability": self.hype_probability,
            "unmet_interests": list(self.unmet_interests),
            "disconnected_claims":
                list(self.disconnected_claims),
            "failing_probes": list(self.failing_probes),
            "simulated_verdict": self.simulated_verdict,
            "corpus_forbidden_hits":
                list(self.corpus_forbidden_hits),
            "replay_stability": self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V233Report:
    relevance = author_relevance()
    connection = paper_connection_visibility()
    spam = spam_probability()
    hype = hype_probability()
    hits = corpus_forbidden_hits()
    clean = not hits
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, relevance=relevance,
        connection=connection, spam=spam, hype=hype,
        forbidden_clean=clean,
    )
    rationale = (
        f"INFO: author interests {len(author_interests())}; "
        f"review probes {len(review_probes())}; claims "
        f"{len(connection_notes())}",
        "INFO: every signal is read from the v23.0-v23.2 "
        "layers; the simulated author is a stress test, not a "
        "claim about real authors",
        f"{'PASS' if relevance >= 0.90 else 'FAIL'}: "
        f"author_relevance {relevance} >= 0.90 (unmet "
        f"{list(unmet_interests())})",
        f"{'PASS' if connection >= 0.90 else 'FAIL'}: "
        f"paper_connection_visibility {connection} >= 0.90 "
        f"(disconnected {list(disconnected_claims())})",
        f"{'PASS' if spam <= 0.10 else 'FAIL'}: "
        f"spam_probability {spam} <= 0.10",
        f"{'PASS' if hype <= 0.10 else 'FAIL'}: "
        f"hype_probability {hype} <= 0.10 (failing probes "
        f"{list(failing_probes())})",
        f"{'PASS' if clean else 'FAIL'}: "
        f"corpus_forbidden_hits {list(hits)} (must be empty)",
        f"INFO: simulated_verdict {simulated_verdict()}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V233Report(
        interest_count=len(author_interests()),
        probe_count=len(review_probes()),
        claim_count=len(connection_notes()),
        author_relevance=relevance,
        paper_connection_visibility=connection,
        spam_probability=spam,
        hype_probability=hype,
        unmet_interests=unmet_interests(),
        disconnected_claims=disconnected_claims(),
        failing_probes=failing_probes(),
        simulated_verdict=simulated_verdict(),
        corpus_forbidden_hits=hits,
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def relevance_section() -> str:
    """Markdown 'Relevance to the base paper' block for the v2
    paper: addressed author interests and anticipated reviewer
    reactions."""
    lines = [
        "## Relevance to the Base Paper",
        "",
        "We test the follow-up against the interests a "
        "base-paper author would weigh and against the two "
        "ways such a follow-up is dismissed - as spam or as "
        "hype.",
        "",
        "### Addressed Author Interests",
        "",
    ]
    for i in author_interests():
        mark = "yes" if i.addressed else "no"
        lines.append(f"- {i.topic} - addressed: {mark}")
    lines += ["", "### Anticipated Reviewer Reactions", ""]
    for p in review_probes():
        lines.append(f"- *{p.question}* {p.reaction}")
    lines.append("")
    return "\n".join(lines)


def build_relevance_artifact() -> dict[str, object]:
    return {
        "schema_version": "v23_3_author_relevance",
        "disclaimer": (
            "Stress-tests the follow-up against a model of a "
            "base-paper author: it must address the author's "
            "interests, connect every claim to a Section 4.6 "
            "open problem, and keep the spam and hype "
            "dismissal probabilities low. The simulated author "
            "is a deterministic stress test built from the "
            "v23.0-v23.2 signals, not a claim about any real "
            "author. No forbidden term appears. Replay-exact."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "author_interests": [
            i.to_dict() for i in author_interests()
        ],
        "connection_notes": [
            n.to_dict() for n in connection_notes()
        ],
        "review_probes": [
            p.to_dict() for p in review_probes()
        ],
        "author_relevance": author_relevance(),
        "paper_connection_visibility":
            paper_connection_visibility(),
        "spam_probability": spam_probability(),
        "hype_probability": hype_probability(),
        "unmet_interests": list(unmet_interests()),
        "disconnected_claims": list(disconnected_claims()),
        "failing_probes": list(failing_probes()),
        "simulated_verdict": simulated_verdict(),
        "corpus_forbidden_hits": list(corpus_forbidden_hits()),
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_IGNORED",
    "VERDICT_RELEVANT",
    "V233Report",
    "build_relevance_artifact",
    "build_report",
    "corpus_forbidden_hits",
    "relevance_section",
]

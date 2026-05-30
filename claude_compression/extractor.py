"""extract_state(chat_history) — deterministic, structural extractor (no LLM, no embeddings).

Input shape: chat_history = [{"role": "user"|"assistant"|"system", "content": str}, ...]

The extractor is intentionally simple and transparent so its choices can be audited:
  * picks ONLY sentences that match explicit lexical/structural cues per field
  * resolves to the LATEST statement when a goal/decision is refined later
  * caps each field's items and tightens phrasing so the whole state fits the 500-token budget
  * never invents content beyond what the chat contains

This is a baseline; the brief does not require sophistication, it requires that compression
preserves the listed epistemic fields. Failures are documented in the evaluation, not patched.
"""
from __future__ import annotations

import re

from state import DesiState, MAX_STATE_TOKENS

GOAL_CUES = ("goal:", "objective:", "we want to", "we need to", "task is to", "the goal is",
             "the aim is", "let's", "we should", "i want to", "i'd like to")
PROBLEM_CUES = ("problem:", "issue:", "open:", "blocked by", "stuck on", "fails because",
                "doesn't work", "not working", "broken", "todo:", "fixme", "open question",
                "still unclear")
FINDING_CUES = ("confirmed:", "verified:", "we found", "measurement shows", "result:",
                "concluded that", "evidence shows", "tested:", "passed:", "works:",
                "succeeded:", "validated:")
DISCARD_CUES = ("rejected:", "discarded:", "we dropped", "decided against", "ruled out",
                "doesn't work because", "wrong approach", "not viable", "rejected because",
                "abandoned:", "scrapped")
DECISION_CUES = ("decision:", "architecture decision:", "we will use", "we'll use",
                 "we chose", "we'll go with", "decided to use", "we picked", "agreed to use",
                 "we standardize on")
CONFLICT_CUES = ("conflict:", "however", "but ", "tension between", "tradeoff:", "trade-off",
                 "disagreement", "tension:", "in conflict with", "contradicts")
REF_PAT = re.compile(r"(?:https?://\S+|\b[A-Za-z_][A-Za-z0-9_/.\-]*\.(?:py|md|json|jsonl|yaml|yml|toml|txt|sh)\b|\barxiv:\S+|\bSSRN[\w ]*\d+|\barXiv:\d+\.\d+)")


def _sentences(text: str) -> list:
    text = re.sub(r"\s+", " ", text or "").strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\[\(])", text)
    return [p.strip() for p in parts if len(p.strip()) > 3]


def _is_chat_history(history) -> bool:
    return isinstance(history, list) and all(
        isinstance(m, dict) and "role" in m and "content" in m for m in history)


def _hit(sent: str, cues) -> bool:
    s = sent.lower()
    return any(c in s for c in cues)


def _shorten(sent: str, max_words: int = 18) -> str:
    s = re.sub(r"\s+", " ", sent).strip().rstrip(".")
    # drop a leading cue if present so the item is denser
    for cue_set in (GOAL_CUES, PROBLEM_CUES, FINDING_CUES, DISCARD_CUES, DECISION_CUES):
        for cue in cue_set:
            if s.lower().startswith(cue):
                s = s[len(cue):].lstrip(" :,-")
                break
    words = s.split()
    if len(words) > max_words:
        s = " ".join(words[:max_words]) + "…"
    return s


def _dedup_keep_last(items: list) -> list:
    """Keep the LATEST mention when an item is restated/refined (paraphrase-tolerant)."""
    out, seen = [], set()
    for item in reversed(items):
        key = re.sub(r"[^a-z0-9 ]", "", item.lower())[:48]
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return list(reversed(out))


def _references(text: str) -> list:
    return list(dict.fromkeys(REF_PAT.findall(text or "")))


def _budget_trim(state: DesiState) -> DesiState:
    """Tighten the state in a fixed order until it fits MAX_STATE_TOKENS. Order is documented
    here so the trade-off is transparent (never tuned to a fixture)."""
    trim_order = [("references", 6), ("discarded_hypotheses", 4),
                  ("open_conflicts", 4), ("open_problems", 5),
                  ("active_goals", 4), ("confirmed_findings", 5),
                  ("architecture_decisions", 6)]
    if state.token_size() <= MAX_STATE_TOKENS:
        return state
    for field_name, keep in trim_order:
        if state.token_size() <= MAX_STATE_TOKENS:
            break
        items = getattr(state, field_name)
        setattr(state, field_name, items[:keep])
    # last resort: shorten remaining strings further
    if state.token_size() > MAX_STATE_TOKENS:
        for field_name in [f for f, _ in trim_order]:
            setattr(state, field_name,
                    [_shorten(x, max_words=10) for x in getattr(state, field_name)])
    return state


def extract_state(chat_history) -> DesiState:
    if not _is_chat_history(chat_history):
        raise TypeError("chat_history must be a list of {'role','content'} dicts")
    state = DesiState()
    refs_all = []
    for msg in chat_history:
        content = msg.get("content", "") or ""
        refs_all.extend(_references(content))
        for sent in _sentences(content):
            if _hit(sent, DECISION_CUES):
                state.architecture_decisions.append(_shorten(sent))
            elif _hit(sent, DISCARD_CUES):
                state.discarded_hypotheses.append(_shorten(sent))
            elif _hit(sent, FINDING_CUES):
                state.confirmed_findings.append(_shorten(sent))
            elif _hit(sent, GOAL_CUES):
                state.active_goals.append(_shorten(sent))
            elif _hit(sent, PROBLEM_CUES):
                state.open_problems.append(_shorten(sent))
            elif _hit(sent, CONFLICT_CUES):
                state.open_conflicts.append(_shorten(sent, max_words=14))
    # close out problems/conflicts that were later resolved (confirmed/decided)
    state.open_problems = [p for p in state.open_problems
                           if not any(p.lower()[:20] in d.lower()
                                      for d in state.architecture_decisions + state.confirmed_findings)]
    # latest-wins dedup
    for f in ("active_goals", "open_problems", "confirmed_findings",
              "discarded_hypotheses", "architecture_decisions", "open_conflicts"):
        setattr(state, f, _dedup_keep_last(getattr(state, f)))
    state.references = list(dict.fromkeys(refs_all))[:8]
    return _budget_trim(state)

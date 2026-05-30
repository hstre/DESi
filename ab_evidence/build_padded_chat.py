"""Build padded versions of case6 by interleaving padding fragments into the chat.

Deterministic: same seed → same padded chat. The interleaving preserves the case6 turn order
and inserts padding fragments AT FIXED POSITIONS between case6 turns. Each padding fragment
is from a labelled pool (prior_iteration / abandoned_tangent / vendor_comparison / repetition
/ exploratory) — none of it is in the case6 GT.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parents[0] / "claude_compression"))

from padding_pool import ALL_POOLS
from padding_pool_extra import EXTRA_POOLS
from state import token_count

SEED = 4242
_FX = _HERE / "fixtures"


def _combined_pool():
    out = {}
    for cat in ALL_POOLS:
        out[cat] = list(ALL_POOLS[cat]) + list(EXTRA_POOLS[cat])
    return out


def _flat_fragments():
    flat = []
    for cat, frags in _combined_pool().items():
        for i, frag in enumerate(frags):
            flat.append({"category": cat, "frag_idx": i, "turns": frag})
    return flat


def build_padded(target_chat_tokens: int, output_id: str) -> dict:
    """Insert padding fragments into case6 chat until target token count is reached."""
    case6 = json.loads((_FX / "case6_long_research_chat.json").read_text())["chat"]
    base_text = "\n".join(m["content"] for m in case6)
    current_tokens = token_count(base_text)
    if current_tokens >= target_chat_tokens:
        raise ValueError(f"case6 already {current_tokens} tokens >= target {target_chat_tokens}")

    rng = random.Random(SEED)
    fragments = _flat_fragments()
    rng.shuffle(fragments)

    # we insert fragments between case6 turns; positions chosen deterministically
    # by spreading insertion points evenly through the case6 timeline
    needed_tokens = target_chat_tokens - current_tokens
    chosen_frags = []
    used_tokens = 0
    frag_idx = 0
    while used_tokens < needed_tokens:
        f = fragments[frag_idx % len(fragments)]
        f_tok = token_count("\n".join(m["content"] for m in f["turns"]))
        chosen_frags.append(f)
        used_tokens += f_tok
        frag_idx += 1

    # insert at evenly spaced positions between case6 turns (after turn 1, then spread)
    n_inserts = len(chosen_frags)
    n_case6 = len(case6)
    positions = sorted({1 + int(i * (n_case6 - 2) / max(1, n_inserts))
                        for i in range(n_inserts)})
    # if we got fewer unique positions than fragments, stack the rest at end
    while len(positions) < n_inserts:
        positions.append(n_case6 - 1)
    positions = positions[:n_inserts]

    # build the padded chat
    out_chat = []
    insert_map = {pos: [] for pos in positions}
    for pos, frag in zip(positions, chosen_frags):
        insert_map[pos].append(frag["turns"])
    for i, turn in enumerate(case6):
        out_chat.append(turn)
        if i in insert_map:
            for frag_turns in insert_map[i]:
                out_chat.extend(frag_turns)

    padded_text = "\n".join(m["content"] for m in out_chat)
    final_tokens = token_count(padded_text)

    # log the padding plan
    category_counts = {}
    for f in chosen_frags:
        category_counts[f["category"]] = category_counts.get(f["category"], 0) + 1
    max_repetition = max(
        sum(1 for f in chosen_frags if f["category"] == cat and f["frag_idx"] == i)
        for cat in _combined_pool() for i in range(len(_combined_pool()[cat]))
    )

    return {
        "id": output_id,
        "type": "long_research_padded",
        "description": f"case6 + realistic padding to ~{target_chat_tokens} tokens. "
                       "Padding fragments from prior_iteration / abandoned_tangent / "
                       "vendor_comparison / repetition / exploratory pools; NOT in GT.",
        "based_on": "case6_long_research",
        "padding_seed": SEED,
        "target_tokens": target_chat_tokens,
        "actual_tokens": final_tokens,
        "n_padding_fragments": n_inserts,
        "padding_category_counts": category_counts,
        "max_fragment_repetition": max_repetition,
        "chat": out_chat,
    }


def main():
    for target, fid in [(30000, "case7a_padded_30k"), (60000, "case7b_padded_60k")]:
        out = build_padded(target, fid)
        path = _FX / f"{fid}_chat.json"
        path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"  {fid}: target={out['target_tokens']} actual={out['actual_tokens']} "
              f"n_frags={out['n_padding_fragments']} max_repeat={out['max_fragment_repetition']}x "
              f"categories={out['padding_category_counts']}")


if __name__ == "__main__":
    main()

"""Under-block red-team — the completeness critic for the slice gate.

The benchmark (`run.py`) proves the gate does not OVER-block (clean slices stay clean). This asks the
adversarial converse: **is there a wrong slice that SURVIVES the unified attack and is allowed to
update?** It enumerates a catalogue of "plausible-wrong-but-passes" families and, for each, measures
two things:

  * ``survives``       — the wrong slice passes ``attack_slice`` (no vector fires) and ``select_mode``
                         allows an update. If True, the gate misses this family.
  * ``caught_when_fed``— the SAME wrongness, with its missing signal actually supplied, IS caught.
                         If True, the check *logic* is sound and the miss is a SIGNAL-quality limit,
                         not a logic hole.

The honest conclusion this is built to expose: the gate's coverage is bounded by the **signals fed to
it**, not by the check logic. Each family is classified:

  * ``irreducible_no_signal`` — the wrongness leaves no structural trace at all (the counter-fact was
    never extracted). No deterministic check can see it; only an external evidence step could.
  * ``signal_quality_upstream`` — a real trace exists but the upstream producer (subject key, source
    family) under-reports it. Fixable by a better producer, at a measured over-fire cost.
  * ``data_model_gap`` — the claim model does not carry the field the check needs (e.g. scope tags).

No LLM. Deterministic and replay-stable, like the checks it attacks.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi_router.governance.report import report_from_snapshot
from desi_router.governance.slice_attack import attack_slice


class _Snap:
    conflicts = ()
    provenance = type("P", (), {"snapshot_hash": "underblock"})()


IRREDUCIBLE = "irreducible_no_signal"
UPSTREAM = "signal_quality_upstream"
DATA_MODEL = "data_model_gap"


@dataclass(frozen=True)
class UnderblockCase:
    key: str
    classification: str
    why: str
    passing: dict           # kwargs producing the wrong-but-passing slice (signal absent)
    fed: dict               # the SAME slice with the missing signal supplied


def _survives_and_updates(**kw) -> bool:
    rep = report_from_snapshot("ub", _Snap(), **kw)
    res = attack_slice(rep, retrieval_available=True)
    return res.survived and res.decision.persistent_state_update_allowed


def _caught(**kw) -> bool:
    rep = report_from_snapshot("ub", _Snap(), **kw)
    res = attack_slice(rep, retrieval_available=True)
    # "caught" = the attack fired OR the gate withheld the update
    return (not res.survived) or (not res.decision.persistent_state_update_allowed)


# the catalogue — each is a slice that LOOKS clean; `passing` omits the signal, `fed` supplies it
CASES: list[UnderblockCase] = [
    UnderblockCase(
        key="supersession_paraphrase",
        classification=UPSTREAM,
        why="a newer claim DOES supersede the slice, but it is phrased with different salient tokens, "
            "so the subject-key lookup never lists it as a newer sibling -> #5 cannot fire. A "
            "better-than-lexical key would catch it, at an over-fire cost the data has not justified.",
        passing=dict(selected_claim_ids=("c1",), newer_sibling_ids=()),
        fed=dict(selected_claim_ids=("c1",), newer_sibling_ids=("c2_newer",)),
    ),
    UnderblockCase(
        key="laundered_provenance",
        classification=UPSTREAM,
        why="three claims trace to ONE origin but carry three distinct family strings, so "
            "independent-source count = 3 and thin-provenance does not fire. An origin-aware family "
            "key would collapse them to one root and flag it.",
        passing=dict(selected_claim_ids=("c1", "c2", "c3"),
                     provenance_sources=("import2021_a", "import2021_b", "import2021_c")),
        fed=dict(selected_claim_ids=("c1", "c2", "c3"),
                 provenance_sources=("import2021", "import2021", "import2021")),
    ),
    UnderblockCase(
        key="out_of_scope_untagged",
        classification=DATA_MODEL,
        why="a claim is valid but belongs to a different project/region; it carries NO scope tag, so "
            "scope-match has nothing to compare and the slice passes. Needs scope tags in the model.",
        passing=dict(selected_claim_ids=("c1",), task_scope=None, claim_scopes=()),
        fed=dict(selected_claim_ids=("c1",), task_scope="eu-west", claim_scopes=("us-east",)),
    ),
    UnderblockCase(
        key="confident_wrong_no_opposition",
        classification=IRREDUCIBLE,
        why="the claim is simply false, but the contradicting fact was never extracted into the graph, "
            "so a full-graph scan finds no opposition -> nothing structural to detect. This is the "
            "documented irreducible floor: only an external evidence step, not a slice check, sees it.",
        passing=dict(selected_claim_ids=("c1",), graph_opposition_ids=()),
        fed=dict(selected_claim_ids=("c1",), graph_opposition_ids=("c1_contradiction",)),
    ),
]


def evaluate(cases: list[UnderblockCase] | None = None) -> dict:
    cases = cases or CASES
    rows = []
    for c in cases:
        rows.append({
            "key": c.key,
            "classification": c.classification,
            "survives": _survives_and_updates(**c.passing),   # the gate misses it (signal absent)
            "caught_when_fed": _caught(**c.fed),               # logic is sound once the signal is fed
        })
    # a baseline genuinely-clean slice MUST survive (control: the gate is not just blocking everything)
    clean_survives = _survives_and_updates(selected_claim_ids=("ok",))
    return {
        "n": len(rows),
        "clean_control_survives": clean_survives,
        "all_misses_are_signal_bounded": all(
            r["caught_when_fed"] for r in rows if r["classification"] != IRREDUCIBLE),
        "rows": rows,
    }


def main() -> int:
    rep = evaluate()
    print(f"Under-block red-team · {rep['n']} families · clean control survives="
          f"{rep['clean_control_survives']}\n")
    for r in rep["rows"]:
        tag = "MISS (gate passes it)" if r["survives"] else "caught"
        fed = "logic catches it once fed" if r["caught_when_fed"] else "NOT caught even when fed"
        print(f"  {r['key']:32s} [{r['classification']:22s}] {tag:22s} | {fed}")
    print(f"\n  all non-irreducible misses are signal-bounded (logic sound): "
          f"{rep['all_misses_are_signal_bounded']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

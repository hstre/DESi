"""Run the dual-layer retrieval probe over the SAME frozen 10 articles (offline replay).

Builds the active DESi state + cold prose for each article, measures anchor precision /
recoverability / cold-fallback / survival, compares against the single-layer compression
probe, and writes: the dual-layer report, narrative retrieval examples (real round-trips
from cold storage), and an honest failure report. Replay-hashes the metrics.

    python probes/wikipedia_dual_layer/run_dual_layer.py
"""
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PREV = _HERE.parent / "wikipedia_epistemic_compression"
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_PREV))
sys.path.insert(0, str(_HERE.parents[1] / "src"))

from desi.core.replay_kernel import replay_hash  # noqa: E402

from dual_layer import build_dual_layer, resolve_locator, resolve_offset  # noqa: E402
from fetch import get_article  # noqa: E402
from freeze import load_frozen  # noqa: E402

_REPORTS = _HERE / "reports"
_RESULTS = _HERE / "results"
_PREV_RESULTS = _PREV / "results" / "wikipedia_probe.jsonl"


def _single_layer_recover() -> dict:
    out = {}
    if _PREV_RESULTS.exists():
        for line in _PREV_RESULTS.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                out[r["pageid"]] = {"recoverability": r["recoverability_proxy"],
                                    "compression": r["compression_ratio"]}
    return out


def run() -> dict:
    _REPORTS.mkdir(parents=True, exist_ok=True)
    _RESULTS.mkdir(parents=True, exist_ok=True)
    frozen = load_frozen()
    layers, rows = [], []
    for sel in frozen["selected"]:
        art = get_article(sel["requested_title"], live=False)   # cache hit; no network
        dl = build_dual_layer(art)
        layers.append(dl)
        rows.append(dl["metrics"])
    rhash = replay_hash({"seed": frozen["seed"], "metrics": rows})
    rows2 = [build_dual_layer(get_article(s["requested_title"], live=False))["metrics"]
             for s in frozen["selected"]]
    replay_stable = replay_hash({"seed": frozen["seed"], "metrics": rows2}) == rhash

    with open(_RESULTS / "dual_layer.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    (_RESULTS / "replay.json").write_text(json.dumps(
        {"replay_hash": rhash, "replay_stable": replay_stable, "n": len(rows)}, indent=2) + "\n",
        encoding="utf-8")

    _dual_report(frozen, rows, rhash, replay_stable)
    _examples_report(layers)
    _failures_report(layers, rows)
    print(f"dual-layer: N={len(rows)} mean_compress={round(st.mean(r['compression_ratio'] for r in rows),3)} "
          f"mean_anchor_prec={round(st.mean(r['anchor_precision'] for r in rows),3)} "
          f"mean_recover={round(st.mean(r['anchor_recoverability'] for r in rows),3)} "
          f"mean_cold={round(st.mean(r['cold_access_rate'] for r in rows),3)} replay_stable={replay_stable}")
    return {"n": len(rows), "replay_stable": replay_stable}


def _dual_report(frozen, rows, rhash, replay_stable):
    single = _single_layer_recover()

    def m(k):
        return round(st.mean(r[k] for r in rows), 3)

    md = [
        "# DESi Wikipedia Dual-Layer Retrieval Probe — report\n",
        "Two layers over the SAME frozen 10 Featured Articles (seed "
        f"{frozen['seed']}, same cache, no new picks): a COLD narrative layer (full prose, "
        "archived) and an ACTIVE DESi state layer (compact epistemic map; each claim / conflict "
        "/ branch / uncertainty unit carries a narrative anchor = section + char offsets + a "
        "short lexical locator). Question: can the compact active layer reliably NAVIGATE back "
        "to the relevant prose? No embeddings, no retrieval engine — deterministic anchors + "
        "replayable offsets only. No DESi-core change.\n",
        f"- Replay hash `{rhash[:16]}…`, stable across two builds: **{replay_stable}**.",
        "",
        "## Single-layer (replace prose) vs dual-layer (navigate prose)\n",
        "| article | type | compress | single-layer recover | dual anchor_precision | "
        "dual anchor_recover | cold_access |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        s = single.get(r["pageid"], {})
        md.append(f"| {r['title'][:24]} | {r['article_type']} | {r['compression_ratio']} | "
                  f"{s.get('recoverability','—')} | {r['anchor_precision']} | "
                  f"{r['anchor_recoverability']} | {r['cold_access_rate']} |")
    md += [
        "",
        f"- Means: compression **{m('compression_ratio')}**, anchor_precision "
        f"**{m('anchor_precision')}** (offset integrity {m('offset_integrity')}), "
        f"anchor_recoverability **{m('anchor_recoverability')}**, cold_access_rate "
        f"**{m('cold_access_rate')}**.",
        f"- Single-layer mean recoverability was ~"
        f"{round(st.mean(v['recoverability'] for v in single.values()),3) if single else '—'} "
        "(entity-anchor coverage, prose gone). The dual layer changes the question: the prose is "
        "NOT gone (it is in cold), and the metric is whether the compact map points back correctly.",
        "",
        "## Per-article dual-layer detail\n",
        "| article | raw_tok | state_tok | anchors | branch_surv | conflict_surv | uncert_surv | "
        "n_units (active) | cold_access |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        md.append(f"| {r['title'][:24]} | {r['raw_tokens']} | {r['state_tokens']} | {r['anchor_count']} | "
                  f"{r['branch_survival']} | {r['conflict_survival']} | {r['uncertainty_survival']} | "
                  f"{r['n_total_units']} ({r['n_active_units']}) | {r['cold_access_rate']} |")
    md += [
        "",
        "## Cold-storage dependency\n",
        f"- `cold_access_rate` = epistemic units with NO active anchor (claims beyond the "
        f"{__import__('dual_layer').CLAIM_BUDGET}-claim budget) ÷ total units — i.e. units that "
        "force a brute cold SCAN rather than a targeted anchored jump. Mean "
        f"**{m('cold_access_rate')}**.",
        "- ALL marker units (branch / conflict / uncertainty) are kept active and anchored, so "
        "they are navigable by a targeted jump; reading their CONTENT always touches cold (that "
        "is the dual-layer design: prose archived, not active).",
        "",
        "## New research questions (measured)\n",
        f"1. **Navigate with little active memory?** Active state is ~{m('compression_ratio')} "
        f"smaller than prose, yet anchors resolve correctly {m('anchor_precision')} of the time "
        "(offset integrity {oi}); navigation works for the units the map holds.".format(oi=m('offset_integrity')),
        f"2. **Conflicts addressable?** conflict_survival mean {m('conflict_survival')} — kept "
        "active and resolvable back to the source span (addressability ≠ nuance; nuance is in cold).",
        f"3. **Alternative narratives reconstructable?** Only as POINTERS — branch_survival "
        f"{m('branch_survival')}: the anchor returns to the branch sentence, but the competing "
        "content must be READ from cold (not reconstructed from the active map).",
        f"4. **Branches led back correctly?** Via offsets, integrity {m('offset_integrity')}; via "
        f"the compact locator, precision {m('anchor_precision')} (collisions on near-duplicate "
        "sentences are the failure mode — see failures report).",
        "5. **Implicit context still lost?** From ACTIVE memory yes (no prose held); but it is "
        "recoverable by following the anchor into cold — the dual layer converts 'lost' into "
        "'archived + addressable'.",
        f"6. **Which operations require cold?** Structural/navigational (count, locate, list "
        "entities, jump-to-source) run on active; any CONTENT read (what it says, the argument, "
        f"the resolution) requires cold. Cold-scan fallback rate {m('cold_access_rate')}.",
        "",
        "## Interpretation (per the rule)\n",
        "- Success here is NOT 'DESi replaces Wikipedia'. It is: **the compact active layer can "
        "function as an epistemic navigation index over archived prose.** On this evidence it "
        f"does for the units it holds (precision {m('anchor_precision')}, offset integrity "
        f"{m('offset_integrity')}), with a {m('cold_access_rate')} cold-scan fallback for claims "
        "beyond budget. The prose stays archived in cold; DESi manages only the active epistemic "
        "state and the pointers back.",
        "",
        "## No overclaiming\n",
        "- Measures epistemic-navigation over archived prose only. NOT understanding, NOT "
        "knowledge-graph replacement, NOT memory. Anchors are lexical/offset, not semantic.",
        "",
        "## Core invariance\n- Peripheral; imports `desi.core.replay_kernel` + the previous probe "
        "READ-ONLY; adds only new files; DESi core byte-identical.",
    ]
    (_REPORTS / "dual_layer_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def _snippet(cold, a, n=220):
    return resolve_offset(a, cold).replace("\n", " ")[:n]


def _examples_report(layers):
    md = ["# Narrative retrieval examples (real round-trips from cold storage)\n",
          "Each example follows an ACTIVE anchor back into the COLD prose via its char offsets. "
          "These are actual slices of the cached article text — the dual layer's 'navigate to "
          "source' in action.\n"]
    # claim -> location ; conflict -> section ; branch -> multiple regions
    shown_claim = shown_conflict = 0
    for dl in layers:
        cold, anchors = dl["cold_text"], dl["anchors"]
        title = dl["metrics"]["title"]
        claims = [a for a in anchors if a["kinds"] == ["claim"]]
        if claims and shown_claim < 3:
            a = claims[0]
            md += [f"### Claim → narrative location — *{title}*",
                   f"- anchor: section {a['section_idx']}, chars [{a['start']}:{a['end']}], "
                   f"locator `{' '.join(a['locator'])}`",
                   f"- resolved prose: “{_snippet(cold, a)}”", ""]
            shown_claim += 1
        confs = [a for a in anchors if "conflict" in a["kinds"]]
        if confs and shown_conflict < 3:
            a = confs[0]
            md += [f"### Conflict → original section — *{title}*",
                   f"- anchor: section {a['section_idx']}, chars [{a['start']}:{a['end']}]",
                   f"- resolved prose: “{_snippet(cold, a)}”", ""]
            shown_conflict += 1
    # a branch spanning multiple narrative regions
    for dl in layers:
        cold, anchors = dl["cold_text"], dl["anchors"]
        branches = [a for a in anchors if "branch" in a["kinds"]]
        if len(branches) >= 2:
            md += [f"### Branch → multiple narrative regions — *{dl['metrics']['title']}*"]
            for a in branches[:3]:
                md += [f"- region (section {a['section_idx']}, chars [{a['start']}:{a['end']}]): "
                       f"“{_snippet(cold, a, 180)}”"]
            md += [""]
            break
    md += ["## Note\n- Offsets index the cached cold text; retrieval is exact on the frozen "
           "snapshot. On a live, edited article the offsets would drift — the lexical locator is "
           "the drift-robust (but lower-precision) fallback."]
    (_REPORTS / "narrative_retrieval_examples.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def _failures_report(layers, rows):
    md = ["# Honest failure report — dual-layer probe\n",
          "What the dual layer loses, mis-resolves, or cannot reconstruct. Measured, not patched.\n",
          "## Anchor errors (locator resolves to the WRONG sentence)\n",
          "Compact lexical locators collide on near-duplicate or boilerplate sentences. Examples "
          "where LOCATOR-mode retrieval lands off the true span:\n"]
    n_err = 0
    for dl in layers:
        cold, anchors, units = dl["cold_text"], dl["anchors"], dl["units"]
        title = dl["metrics"]["title"]
        for a in anchors:
            best, correct = resolve_locator(a, units)
            if not correct and best is not None and n_err < 8:
                true = cold[a["start"]:a["end"]].replace("\n", " ")[:120]
                got = best["text"].replace("\n", " ")[:120]
                md += [f"- *{title}* locator `{' '.join(a['locator'])}` →",
                       f"    - TRUE: “{true}”",
                       f"    - GOT : “{got}”"]
                n_err += 1
    if n_err == 0:
        md += ["- (none on this sample — locators resolved uniquely; this can change with more "
               "boilerplate-heavy articles)."]
    md += [
        "",
        "## Units with no active anchor (require a cold SCAN)\n",
        f"- Claims beyond the budget are dropped from the active map; they have no pointer and "
        "would need a full cold scan to find. Per article (dropped / total units):",
        *[f"  - {r['title'][:30]}: {r['n_total_units'] - r['n_active_units']} / {r['n_total_units']} "
          f"(cold_access_rate {r['cold_access_rate']})" for r in rows],
        "",
        "## Non-reconstructable / lost from active memory\n",
        "- **Implicit context & cultural frames:** never in the active map (no prose); only "
        "reachable by reading cold, and some implicit cross-references are not localizable to a "
        "single span at all.",
        "- **Conflict resolution / branch arguments:** the active map marks WHERE a conflict or "
        "alternative narrative is, never WHAT it concludes — the reasoning lives only in cold.",
        "- **Nested / reference-heavy sections:** sentence-level anchors flatten nested narrative "
        "structure; a single offset cannot represent a multi-paragraph argument.",
        "- **Survival is addressability, not preservation:** branch/conflict/uncertainty "
        "'survival' means the source span is reachable, NOT that its nuance is retained in active "
        "memory. That nuance is archived (cold), not active.",
        "",
        "## Honest limits\n",
        "- Detection is fixed lexical/structural heuristics (no embeddings): paraphrastic "
        "conflicts and implicit branches are missed; cue words used non-epistemically false-"
        "positive. Offsets are exact only on the frozen cache (fragile to edits). Locators are "
        "6-token lexical keys (collision-prone). The claim budget and locator length were fixed "
        "before the run and not tuned to results.",
    ]
    (_REPORTS / "honest_failures.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run()

"""Steps 2 & 4: persist + hash every input and FREEZE before the model run.

Reads the frozen claim files (from ``extract.py``), builds the slices for all
cases and arms (``slice_builder``), gates the wrong arms through the matcher with
auditing, and writes a single frozen manifest:

    frozen/manifest.json

containing, per (case, arm): the rendered slice, its content hash, token length,
and the matcher decision; plus the pre-registration hash. This file is the
contract the arm runner consumes — nothing downstream may change an input
without changing (and re-freezing) this manifest. Deterministic and offline.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from slice_builder import FROZEN_DIR, build_arms  # noqa: E402
from slice_matcher import content_hash_text, default_token_count, render_slice  # noqa: E402

from case_schema import load_cases  # noqa: E402

MANIFEST = FROZEN_DIR / "manifest.json"
PREREG = HERE / "PREREGISTRATION.md"
AUDIT_SINK = FROZEN_DIR / "match_audit.jsonl"


def prereg_hash() -> str:
    return content_hash_text(PREREG.read_text(encoding="utf-8"))


def build_manifest(frozen_dir: Path = FROZEN_DIR, audit_sink: Path = AUDIT_SINK) -> dict:
    cases = load_cases()
    entries: dict[str, dict] = {}
    for cid, case in cases.items():
        arms = build_arms(
            cid, case.pass_id, case.permuted_donor, case.plausible_donor,
            frozen_dir=frozen_dir, audit_sink=audit_sink,
        )
        arm_entries = {}
        for arm, a in arms.items():
            rendered = render_slice(a.slice)
            arm_entries[arm] = {
                "slice_hash": a.slice_hash,
                "matcher_ok": a.matcher_ok,
                "token_length": default_token_count(rendered),
                "n_claims": len(a.slice.claims),
                "rendered": rendered,
            }
        # the raw arm carries no slice
        arm_entries["raw"] = {"slice_hash": "", "matcher_ok": None,
                              "token_length": 0, "n_claims": 0, "rendered": ""}
        entries[cid] = {
            "pass_id": case.pass_id,
            "domain": case.domain,
            "permuted_donor": case.permuted_donor,
            "plausible_donor": case.plausible_donor,
            "arms": arm_entries,
        }
    manifest = {
        "prereg_hash": prereg_hash(),
        "cases": entries,
    }
    manifest["manifest_hash"] = content_hash_text(
        json.dumps(manifest, sort_keys=True, ensure_ascii=False)
    )
    return manifest


def main() -> None:
    FROZEN_DIR.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"froze {len(manifest['cases'])} cases -> {MANIFEST.name}")
    print(f"prereg_hash   = {manifest['prereg_hash'][:12]}")
    print(f"manifest_hash = {manifest['manifest_hash'][:12]}")
    for cid, e in manifest["cases"].items():
        toks = {a: v["token_length"] for a, v in e["arms"].items() if a != "raw"}
        print(f"  {cid}: tokens {toks}")


if __name__ == "__main__":
    main()

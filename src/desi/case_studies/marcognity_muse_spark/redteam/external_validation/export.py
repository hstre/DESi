"""Blind annotation export: workbook for two independent annotators + manifest.

The export carries the candidate sentence and its document context, and EMPTY fields
for the annotators to fill. It contains no rule output and no gold — annotators label
independently. Gold-sentence and gold-document are captured separately, plus the
effect-size locus and the true-error-vs-missing-local-evidence distinction.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

# controlled vocabularies (mirrored in the annotation guidelines)
CLASS_VALUES = ("SIG", "clean_no_significance", "clean_no_magnitude",
                "clean_effect_size_present", "null_result", "boundary")
LOCUS_VALUES = ("same_sentence", "adjacent_sentence", "table_or_figure",
                "ci_only", "absent")
ERROR_TYPE_VALUES = ("true_epistemic_error", "missing_local_evidence_present_elsewhere",
                     "na")

# empty fields the annotator fills (blind)
ANNOTATION_FIELDS = (
    "gold_sentence_class",      # judged on the sentence alone (what a sentence rule sees)
    "gold_document_class",      # judged with full document context (tables, adjacent text)
    "effect_size_locus",        # where the effect size lives (LOCUS_VALUES)
    "error_type",               # ERROR_TYPE_VALUES: real error vs evidence-present-elsewhere
    "confidence_1to3",
    "annotator_notes",
)
_CONTEXT_FIELDS = (
    "claim_id", "pmcid", "section_type", "section_title", "strata",
    "sentence", "prev_sentence", "next_sentence", "paragraph_text",
    "referenced_tables", "referenced_figures",
)


def _flat(cand: dict) -> dict:
    def refs(key):
        return " || ".join(f"{r['label']}: {r['caption']}".strip(": ")
                           for r in cand.get(key, []))
    return {
        "claim_id": cand["claim_id"], "pmcid": cand["pmcid"],
        "section_type": cand.get("section_type", ""),
        "section_title": cand.get("section_title", ""),
        "strata": ",".join(cand.get("strata", [])),
        "sentence": cand["sentence"], "prev_sentence": cand.get("prev_sentence", ""),
        "next_sentence": cand.get("next_sentence", ""),
        "paragraph_text": cand.get("paragraph_text", ""),
        "referenced_tables": refs("referenced_tables"),
        "referenced_figures": refs("referenced_figures"),
    }


def write_annotation_workbook(claims: list[dict], out_dir: Path,
                              annotators=("A", "B")) -> list[Path]:
    """Write one blind CSV per annotator + a full-fidelity claims.json. Returns paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    header = list(_CONTEXT_FIELDS) + list(ANNOTATION_FIELDS)
    paths = []
    for ann in annotators:
        p = out_dir / f"annotation_{ann}.csv"
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=header)
            w.writeheader()
            for c in claims:
                row = _flat(c)
                row.update({k: "" for k in ANNOTATION_FIELDS})
                w.writerow(row)
        paths.append(p)
    (out_dir / "claims.json").write_text(
        json.dumps(claims, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return paths


def write_manifest(pmcids: list[str], stage: str, path: Path) -> None:
    path.write_text(json.dumps({"stage": stage, "n_documents": len(pmcids),
                                "pmcids": sorted(pmcids)}, indent=2) + "\n",
                    encoding="utf-8")


def write_codebook(path: Path) -> None:
    path.write_text(json.dumps({
        "gold_sentence_class": list(CLASS_VALUES),
        "gold_document_class": list(CLASS_VALUES),
        "effect_size_locus": list(LOCUS_VALUES),
        "error_type": list(ERROR_TYPE_VALUES),
        "confidence_1to3": [1, 2, 3],
        "note": "Fill blind, independently per annotator. gold_sentence_class uses the "
                "sentence ALONE; gold_document_class uses tables + adjacent context. "
                "error_type distinguishes a real epistemic error (absent effect size "
                "anywhere) from evidence merely missing locally but present elsewhere.",
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


__all__ = ["CLASS_VALUES", "LOCUS_VALUES", "ERROR_TYPE_VALUES", "ANNOTATION_FIELDS",
           "write_annotation_workbook", "write_manifest", "write_codebook"]

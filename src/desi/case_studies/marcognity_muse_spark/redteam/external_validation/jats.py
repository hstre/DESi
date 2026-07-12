"""Parse JATS full-text XML into sections / paragraphs / sentences / tables (stdlib).

The sentence splitter is FROZEN (v1) and versioned via ``SPLITTER_VERSION`` — the
protocol requires a fixed segmentation so annotation units and rule application align.
Do not change it without bumping the version and re-freezing.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

SPLITTER_VERSION = "extval-sent-v1"

# abbreviations whose trailing period must NOT end a sentence
_ABBREV = ("e.g", "i.e", "vs", "cf", "Fig", "fig", "Figs", "Eq", "eq", "No", "no",
           "Dr", "Prof", "et al", "approx", "ref", "Ref", "Tab", "tab", "ca", "Inc",
           "Ltd", "St", "Jr", "Sr", "al", "Sci", "Med", "J", "vol", "pp", "p")
_PLACEHOLD = ""


def split_sentences(text: str) -> list[str]:
    """Frozen v1 splitter: protects decimals, %, and known abbreviations, then splits
    on sentence-final punctuation followed by whitespace and a capital / paren / digit."""
    t = re.sub(r"\s+", " ", text).strip()
    if not t:
        return []
    # protect decimals like 0.05 and abbreviations' periods
    t = re.sub(r"(\d)\.(\d)", rf"\1{_PLACEHOLD}\2", t)
    for ab in _ABBREV:
        t = re.sub(rf"(?<![A-Za-z]){re.escape(ab)}\.", ab + _PLACEHOLD, t)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(\[\"“‘])", t)
    return [p.replace(_PLACEHOLD, ".").strip() for p in parts if p.strip()]


def _text(el: ET.Element | None) -> str:
    if el is None:
        return ""
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


@dataclass
class Paragraph:
    id: str
    section_type: str
    section_title: str
    text: str
    sentences: list[str]
    table_refs: list[str] = field(default_factory=list)
    fig_refs: list[str] = field(default_factory=list)


@dataclass
class Document:
    pmcid: str
    title: str
    journal: str
    article_type: str
    sections: list[dict]
    paragraphs: list[Paragraph]
    tables: dict[str, dict]
    figures: dict[str, dict]


def _refs(p_el: ET.Element, ref_type: str) -> list[str]:
    out = []
    for x in p_el.iter("xref"):
        if x.get("ref-type") == ref_type and x.get("rid"):
            out.extend(x.get("rid").split())
    return out


def parse(xml_str: str, pmcid: str = "") -> Document:
    root = ET.fromstring(xml_str)
    art_type = root.get("article-type", "")
    title = _text(root.find(".//article-meta//article-title"))
    journal = _text(root.find(".//journal-meta//journal-title"))

    tables: dict[str, dict] = {}
    for tw in root.iter("table-wrap"):
        tid = tw.get("id") or f"tbl{len(tables)}"
        tables[tid] = {"id": tid, "label": _text(tw.find("label")),
                       "caption": _text(tw.find("caption")), "text": _text(tw.find("table"))}
    figures: dict[str, dict] = {}
    for fg in root.iter("fig"):
        fid = fg.get("id") or f"fig{len(figures)}"
        figures[fid] = {"id": fid, "label": _text(fg.find("label")),
                        "caption": _text(fg.find("caption"))}

    paragraphs: list[Paragraph] = []
    sections: list[dict] = []
    # abstract (front matter) — importance claims often surface here
    for ab in root.findall(".//front//abstract"):
        for p in ab.iter("p"):
            txt = _text(p)
            if txt:
                paragraphs.append(Paragraph(p.get("id") or f"abs{len(paragraphs)}",
                                            "abstract", "Abstract", txt,
                                            split_sentences(txt), _refs(p, "table"),
                                            _refs(p, "fig")))
    body = root.find(".//body")
    if body is not None:
        for sec in body.iter("sec"):
            stype = sec.get("sec-type") or _text(sec.find("title")) or "body"
            stitle = _text(sec.find("title"))
            sec_paras = []
            for p in sec.findall("p"):
                txt = _text(p)
                if not txt:
                    continue
                pid = p.get("id") or f"auto{len(paragraphs)}"
                para = Paragraph(pid, stype, stitle, txt, split_sentences(txt),
                                 _refs(p, "table"), _refs(p, "fig"))
                paragraphs.append(para)
                sec_paras.append(pid)
            sections.append({"type": stype, "title": stitle, "paragraph_ids": sec_paras})

    return Document(pmcid, title, journal, art_type, sections, paragraphs, tables, figures)


__all__ = ["SPLITTER_VERSION", "split_sentences", "Paragraph", "Document", "parse"]

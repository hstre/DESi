"""Network-free tests for the external-validation tooling (parser/candidates/export)."""
from __future__ import annotations

from desi.case_studies.marcognity_muse_spark.redteam.external_validation import (
    candidates, export, jats, sampling,
)

_FIXTURE = """<article article-type="research-article">
 <front>
  <journal-meta><journal-title>J Test</journal-title></journal-meta>
  <article-meta>
   <article-title>Effect of X on Y in adults</article-title>
   <abstract><p>The reduction was statistically significant (p &lt; 0.001) and clinically important.</p></abstract>
  </article-meta>
 </front>
 <body>
  <sec sec-type="methods"><title>Methods</title><p>We computed p-values and 95% confidence intervals.</p></sec>
  <sec sec-type="results"><title>Results</title>
   <p id="p1">Group A improved (p = 0.002), see <xref ref-type="table" rid="t1">Table 1</xref>. The effect size was small (d = 0.1).</p></sec>
  <sec sec-type="discussion"><title>Discussion</title>
   <p id="p2">The intervention is clinically meaningful and important.</p></sec>
 </body>
 <floats-group>
  <table-wrap id="t1"><label>Table 1</label><caption><p>Outcomes by group.</p></caption><table><tr><td>d = 0.1</td></tr></table></table-wrap>
 </floats-group>
</article>"""


def test_splitter_protects_decimals_and_abbreviations():
    s = jats.split_sentences("Group A improved (p = 0.002), see Table 1. The effect was small.")
    assert len(s) == 2 and s[0].endswith("Table 1.")
    assert jats.split_sentences("Values were e.g. 0.5 and 0.7 in the cohort.") == \
        ["Values were e.g. 0.5 and 0.7 in the cohort."]


def test_parse_sections_abstract_and_tables():
    doc = jats.parse(_FIXTURE, "PMC0")
    assert doc.article_type == "research-article"
    assert doc.title.startswith("Effect of X")
    stypes = {p.section_type for p in doc.paragraphs}
    assert {"abstract", "results", "discussion", "methods"} <= stypes
    assert "t1" in doc.tables and "Outcomes" in doc.tables["t1"]["caption"]
    p1 = next(p for p in doc.paragraphs if p.id == "p1")
    assert p1.table_refs == ["t1"] and len(p1.sentences) == 2


def test_candidates_only_from_reporting_sections_with_context():
    doc = jats.parse(_FIXTURE, "PMC0")
    cands = candidates.find_candidates(doc)
    secs = {c["section_type"] for c in cands}
    assert "methods" not in secs                      # methods excluded
    assert secs <= {"abstract", "results", "discussion"}
    # the results sentence referencing Table 1 carries the table caption as context
    tbl = [c for c in cands if c["referenced_tables"]]
    assert tbl and "Outcomes" in tbl[0]["referenced_tables"][0]["caption"]
    # strata are tagged (not only p-value)
    allstrata = {s for c in cands for s in c["strata"]}
    assert "p_value" in allstrata and ("relevance" in allstrata or "effect_size" in allstrata)


def test_select_stratified_caps_and_is_deterministic():
    import random
    doc = jats.parse(_FIXTURE, "PMC0")
    cands = candidates.find_candidates(doc)
    a = candidates.select_stratified(cands, 2, random.Random(1))
    b = candidates.select_stratified(cands, 2, random.Random(1))
    assert len(a) <= 2 and {c["sentence"] for c in a} == {c["sentence"] for c in b}


def test_eligibility_excludes_reviews_and_protocols():
    ok, _ = sampling.is_eligible(jats.parse(_FIXTURE, "PMC0"))
    assert ok
    review = _FIXTURE.replace('article-type="research-article"', 'article-type="review-article"')
    assert not sampling.is_eligible(jats.parse(review, "PMC1"))[0]
    proto = _FIXTURE.replace("Effect of X on Y in adults", "Study protocol for a trial")
    assert not sampling.is_eligible(jats.parse(proto, "PMC2"))[0]


def test_export_workbook_is_blind(tmp_path):
    claims = [{"claim_id": "C0001", "pmcid": "PMC0", "section_type": "results",
               "section_title": "Results", "strata": ["p_value"], "sentence": "S.",
               "prev_sentence": "", "next_sentence": "", "paragraph_text": "S.",
               "referenced_tables": [], "referenced_figures": []}]
    paths = export.write_annotation_workbook(claims, tmp_path)
    assert len(paths) == 2                            # two independent annotators
    head = paths[0].read_text().splitlines()[0]
    for f in export.ANNOTATION_FIELDS:
        assert f in head
    # blind: the row has empty annotation cells, no gold, no rule output
    row = paths[0].read_text().splitlines()[1]
    assert row.endswith(",,,,,")


def test_build_stage_excludes_prior_pmcids(monkeypatch):
    pages = {p: {"hit_count": 2, "next_cursor": "END",
                 "results": [{"pmcid": "PMC_A", "title": "", "pub_types": [], "pmid": "",
                              "journal": "", "year": ""},
                             {"pmcid": "PMC_B", "title": "", "pub_types": [], "pmid": "",
                              "journal": "", "year": ""}]} for p in sampling.SEED_PHRASES}
    monkeypatch.setattr(sampling.europepmc, "search",
                        lambda phrase, page_size=25, cursor="*": pages[phrase])
    result = sampling.build_stage(5, 10, 2, __import__("random").Random(0),
                                  exclude_pmcids={"PMC_A"},
                                  fetch=lambda pmcid: _FIXTURE)
    assert "PMC_A" not in result["pmcids"] and "PMC_B" in result["pmcids"]
    assert all(c["claim_id"].startswith("C") for c in result["claims"])

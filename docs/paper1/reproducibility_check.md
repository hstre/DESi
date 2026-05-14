# Paper 1 v0.1 — reproducibility check

Independent fresh-clone reproduction of the Paper 1 v0.1 deliverable,
run against the published tip of `release/paper1-representation-gap`.

## Procedure

```
git clone --branch release/paper1-representation-gap --single-branch \
    <origin> /tmp/desi-fresh-clone
cd /tmp/desi-fresh-clone
python3 docs/paper1/assemble_paper_v0_1.py
```

The clone was performed against the live remote, into an empty
temporary directory, with no carry-over from the working tree.

## Pre-run state of the fresh clone

`docs/paper1/` after clone (no `.docx`, no base64 sidecar, no
`reproducibility_check.md`):

```
assemble_paper_v0_1.py
citation_audit_v0_1.md
decode_docx.py
outline_representation_gap.md
```

This is the published v0.1 surface: outline, assembler, audit log,
and decoder. The binary `.docx` is excluded by `.gitignore` line 43.
The base64 sidecar parts are not present on the remote branch
(transport channel cannot carry 30 KB-per-file opaque payloads
faithfully); the decoder falls through to the assembler in that case.

## Assembler run

```
$ python3 docs/paper1/assemble_paper_v0_1.py
wrote /tmp/desi-fresh-clone/docs/paper1/DESi_Paper_1_Representation_Gap_v0_1.docx
wrote /tmp/desi-fresh-clone/docs/paper1/citation_audit_v0_1.md
paragraphs=62  uncited=0  duplicated=0  unused_artefacts=0
```

Exit code 0. No `MISSING ARTEFACTS:` message, which means all
eighteen artefact codes in `ARTEFACTS` resolve to existing files at
the cited paths (Appendix A check). Run takes < 1 second; only
dependency is `python-docx`.

## Output verification

| Check                          | Expected           | Observed           | Result |
|---|---|---|---|
| DOCX file exists               | yes                | yes                | PASS   |
| DOCX size (bytes)              | non-zero, plausible | 45 217             | PASS   |
| DOCX magic header              | `PK\x03\x04` (ZIP)   | `PK\x03\x04`         | PASS   |
| Paragraph count                | 62                 | 62                 | PASS   |
| Uncited paragraphs             | 0                  | 0                  | PASS   |
| Duplicated text spans          | 0                  | 0                  | PASS   |
| Unused artefacts               | 0                  | 0                  | PASS   |

DOCX SHA-256 in this run:
`c2126701c6a0ee4c8309dd131a1977e4ca5a190b7ff88df895bf9410377374c2`

## Byte-level non-determinism (expected)

The DOCX is **content-identical** but **not byte-identical** to
previous runs. `python-docx` embeds a thumbnail that carries a
fresh creation timestamp on every run, and assigns numeric rIds
in dictionary-iteration order, so the inner ZIP entries differ
between two consecutive invocations of the assembler.

For byte-identical reproduction, decode from the sidecar via
`decode_docx.py` (requires `.b64.part01` + `.b64.part02` to be
present locally). Content-equality is the load-bearing claim;
byte-equality is decorative.

## Audit log spot-check

The fresh-clone `citation_audit_v0_1.md` matches the published audit
on counts:

```
## Uncited paragraphs
- None. Every paragraph carries at least one citation.

## Duplicated text spans
- None. No two paragraphs share normalised text under
  case-insensitive whitespace-collapsed comparison.

## Unused artefacts
- None. Every registered artefact is cited at least once.
```

Per-artefact use counts (top of the table): RGR=14, EN4E=10, ERC=9,
PFD=8, OUT=8, P0=7, PPD=7, EN2=6, BC=6, EN1=5, EN5E=5, C1E=4,
C2E=4, EN3=4, EN4R=3, EN5R=3, C1P=1, C2P=1.

## Conclusion

A reader who pulls `release/paper1-representation-gap` and runs
`python3 docs/paper1/assemble_paper_v0_1.py` reconstructs Paper 1
v0.1 deterministically at the content level: 62 cited paragraphs,
0 uncited, 0 duplicated, 0 unused artefacts. The deliverable is
self-contained on the branch.

No DESi source change. No new experiments. Documentation only.

"""Decode the base64 sidecar back to a .docx (or fall back to the assembler).

Usage:
    python3 docs/paper1/decode_docx.py

Reconstructs docs/paper1/DESi_Paper_1_Representation_Gap_v0_1.docx
byte-identically by concatenating the split base64 parts when they
are present. If neither the parts nor the single-file sidecar are
available locally, the decoder defers to `assemble_paper_v0_1.py`,
which regenerates the .docx from the cited artefacts in the repo.

The sidecar exists because the .docx is a binary zip that cannot be
transmitted through a JSON-text channel directly. The .b64 form is
diff-friendly and recoverable. The split-into-parts layout keeps each
upload payload under the inline-content size budget; the parts
concatenate losslessly because base64 line breaks are insignificant.
"""
import base64
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
PARTS = [
    ROOT / "DESi_Paper_1_Representation_Gap_v0_1.docx.b64.part01",
    ROOT / "DESi_Paper_1_Representation_Gap_v0_1.docx.b64.part02",
]
SINGLE = ROOT / "DESi_Paper_1_Representation_Gap_v0_1.docx.b64"
ASSEMBLER = ROOT / "assemble_paper_v0_1.py"
OUT = ROOT / "DESi_Paper_1_Representation_Gap_v0_1.docx"


def _decode_from_sidecar() -> bytes | None:
    if SINGLE.is_file():
        return base64.b64decode(SINGLE.read_text())
    if all(p.is_file() for p in PARTS):
        return base64.b64decode("".join(p.read_text() for p in PARTS))
    return None


def main() -> int:
    raw = _decode_from_sidecar()
    if raw is not None:
        OUT.write_bytes(raw)
        print(f"wrote {OUT} ({len(raw)} bytes) from sidecar")
        return 0
    if ASSEMBLER.is_file():
        print("sidecar parts absent; deferring to assemble_paper_v0_1.py")
        return subprocess.call([sys.executable, str(ASSEMBLER)])
    print(
        "ERROR: neither sidecar parts nor assemble_paper_v0_1.py present. "
        "Pull the release/paper1-representation-gap branch in full.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

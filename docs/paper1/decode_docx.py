"""Decode the base64 sidecar back to a .docx.

Usage:
    python3 docs/paper1/decode_docx.py

Reconstructs docs/paper1/DESi_Paper_1_Representation_Gap_v0_1.docx
byte-identically by concatenating the split base64 parts.

This sidecar exists because the .docx is a binary zip that cannot be
transmitted through a JSON-text channel directly. The .b64 form is
diff-friendly and recoverable. It is split into two parts to keep
each upload payload under the inline-content size budget; the parts
concatenate losslessly because base64 line breaks are insignificant.
"""
import base64
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
PARTS = [
    ROOT / "DESi_Paper_1_Representation_Gap_v0_1.docx.b64.part01",
    ROOT / "DESi_Paper_1_Representation_Gap_v0_1.docx.b64.part02",
]
OUT = ROOT / "DESi_Paper_1_Representation_Gap_v0_1.docx"

# Backward compatibility: if a single-file .b64 exists, prefer it.
single = ROOT / "DESi_Paper_1_Representation_Gap_v0_1.docx.b64"
if single.is_file():
    combined = single.read_text()
else:
    combined = "".join(p.read_text() for p in PARTS)

raw = base64.b64decode(combined)
OUT.write_bytes(raw)
print(f"wrote {OUT} ({len(raw)} bytes)")

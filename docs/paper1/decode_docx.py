"""Decode the base64 sidecar back to a .docx.

Usage:
    python3 docs/paper1/decode_docx.py

Reads docs/paper1/DESi_Paper_1_Representation_Gap_v0_1.docx.b64 and
writes docs/paper1/DESi_Paper_1_Representation_Gap_v0_1.docx
byte-identically.

This sidecar exists because the .docx is a binary zip that cannot be
transmitted through a JSON-text channel directly. The .b64 form is
diff-friendly and recoverable.
"""
import base64
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
B64 = ROOT / "DESi_Paper_1_Representation_Gap_v0_1.docx.b64"
OUT = ROOT / "DESi_Paper_1_Representation_Gap_v0_1.docx"

raw = base64.b64decode(B64.read_text())
OUT.write_bytes(raw)
print(f"wrote {OUT} ({len(raw)} bytes)")

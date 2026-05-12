"""Inspect tables and formulas extracted from a PDF.

NOTE on server-side limits (as of TurboOCR v2.2.3):
  - Tables: the server detects the *region* (you get a `bounding_box` and
    row-major OCR'd `text`), but does NOT emit cell structure. `Table.html`
    and `Table.cells` are always None until a future server release ships
    table-structure-recognition.
  - Formulas: same story. The server detects the region but does NOT emit
    LaTeX source. `Formula.latex` is always None for now.

The SDK shape is forward-compatible: when the server starts emitting
structure, `html` / `cells` / `latex` will populate and your code stays
the same.
"""

from pathlib import Path

from turboocr import Client

PDF = Path(__file__).parent / "sample" / "acme_invoice.pdf"

client = Client()
response = client.recognize_pdf(PDF, include_blocks=True)

print(
    f"pages={len(response.pages)} "
    f"tables={len(response.tables)} formulas={len(response.formulas)}"
)

if response.tables:
    t = response.tables[0]
    snippet = t.text[:80].replace("\n", " ") if t.text else ""
    print(f"first table: aabb={t.bounding_box.aabb} html={t.html} cells={t.cells}")
    print(f"  text preview: {snippet!r}")

# Output:
# pages=2 tables=1 formulas=0
# first table: aabb=(128, 890, 1140, 1422) html=None cells=None
#   text preview: '# Description Qty Unit price Amount 1 Industrial-grade Rocket Skates (model RS-9'

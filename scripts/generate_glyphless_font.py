"""Generate src/turboocr/_data/glyphless.ttf.

Produces a minimal TTF used as the invisible-text-overlay font in
make_searchable_pdf. The font has:

- a single zero-mark glyph at fixed width (500 units / 1000 upm)
- a `cmap` covering the full Basic Multilingual Plane (U+0001..U+FFFF)
  with every codepoint pointed at that one glyph
- the metric tables PDF readers need to compute text-selection bboxes

The glyph itself is empty — render-mode 3 (invisible) hides it anyway,
and the visible page is the original scan. This is the same trick
Tesseract's GlyphLessFont uses; see
https://github.com/tesseract-ocr/tesseract/blob/main/src/api/pdfrenderer.cpp

Run once from the repo root:

    uv run --extra dev python scripts/generate_glyphless_font.py

Commit the resulting .ttf alongside the source. The wheel bundles it via
hatch's package-data settings; runtime loads it with importlib.resources.
"""

from __future__ import annotations

from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables import _c_m_a_p

OUT = Path(__file__).resolve().parents[1] / "src/turboocr/_data/glyphless.ttf"

UPM = 1000              # units per em
UNIFORM_WIDTH = 500     # all glyphs the same width
ASCENT = 900
DESCENT = -100
BMP_END = 0x10000       # exclusive — covers U+0000..U+FFFF


def build() -> None:
    fb = FontBuilder(UPM, isTTF=True)

    glyph_order = [".notdef", "glyph1"]
    fb.setupGlyphOrder(glyph_order)

    pen = TTGlyphPen(None)
    fb.setupGlyf({name: pen.glyph() for name in glyph_order})

    # Build cmap manually. FontBuilder's setupCharacterMap defaults to
    # format 4 which overflows when one glyph covers all 65k BMP codepoints,
    # and format 12 stores every codepoint individually (~800 KB). Format 13
    # is the "many-to-one range" variant: a single (start, end, glyphID)
    # group encodes "every char in [start..end] maps to glyphID" — exactly
    # the shape we need. Same trick Tesseract uses for GlyphLessFont.
    cmap_table = _c_m_a_p.table__c_m_a_p()
    cmap_table.tableVersion = 0
    sub = _c_m_a_p.CmapSubtable.getSubtableClass(13)()
    sub.format = 13
    sub.reserved = 0
    sub.length = 0
    sub.language = 0
    sub.platformID = 3
    sub.platEncID = 10  # Microsoft Unicode UCS-4 (full Unicode)
    sub.cmap = {cp: "glyph1" for cp in range(1, BMP_END)}
    cmap_table.tables = [sub]
    fb.font["cmap"] = cmap_table

    fb.setupHorizontalMetrics(dict.fromkeys(glyph_order, (UNIFORM_WIDTH, 0)))
    fb.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT)
    fb.setupOS2(
        sTypoAscender=ASCENT,
        sTypoDescender=DESCENT,
        usWinAscent=ASCENT,
        usWinDescent=-DESCENT,
    )
    fb.setupNameTable(
        {
            "familyName": "TurboOcrGlyphless",
            "styleName": "Regular",
            "uniqueFontIdentifier": "turboocr-glyphless-1.0",
            "fullName": "TurboOcrGlyphless",
            "psName": "TurboOcrGlyphless",
        }
    )
    fb.setupPost()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fb.save(OUT.as_posix())
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    build()

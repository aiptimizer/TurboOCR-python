# Searchable PDF internals

A searchable PDF looks identical to the original but its text can be
selected, copied, and indexed. The SDK adds an invisible text layer on
top of the original page using PDF text rendering mode `3` — fill none,
stroke none. The viewer's text-extraction layer walks that stream as if
it were normal text.

## Coordinates

Each OCR'd word is placed at its OCR bounding box. The higher the
`dpi=` you pass, the tighter the alignment between visible and invisible
streams.

## The bundled glyphless font

Every PDF text-drawing op must reference a font. The SDK bundles a
~760 B glyphless TTF that has one zero-mark glyph and a cmap covering
every Basic Multilingual Plane codepoint (U+0001..U+FFFF). Every char
maps to that single invisible glyph. Same technique as Tesseract's
[`GlyphLessFont`](https://github.com/tesseract-ocr/tesseract/blob/main/src/api/pdfrenderer.cpp)
and Adobe Acrobat's "searchable image" mode. Text extraction works
because the cmap is a reversible Unicode mapping; the glyph itself is
never rendered.

## Size overhead

Embedded font ~10 KB compressed. Invisible text stream scales with OCR
output: a 2-page invoice with ~70 items adds about 18 KB. Negligible
on multi-MB scans.

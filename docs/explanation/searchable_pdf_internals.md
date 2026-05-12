# Searchable PDF internals

A *searchable* PDF looks identical to the original — same fonts, same
images, same scanned artifacts — but its text can be selected, copied,
and indexed by full-text search engines. This page explains how that
trick works and why it produces the constraints the SDK exposes.

## The invisible text overlay

The original page already renders fine. What it lacks is a *text layer* —
a separate stream of glyphs that the viewer can hit-test against your
mouse selection. The searchable-PDF generator does not replace anything
on the original page; it adds a new content stream on top of it that
draws OCR'd text at the same coordinates as the visible glyphs, in an
**invisible** rendering mode (PDF text rendering mode `3` — fill none,
stroke none).

The viewer's text-extraction layer walks the invisible text stream as if
it were normal text. Your eyes still see the original page underneath
because the invisible glyphs paint zero ink.

## Why coordinates matter

For the overlay to be useful, each OCR'd word has to be placed at the
same coordinates as the visible word, at roughly the same size. That
geometry comes directly from the OCR text items' bounding boxes. If the
bounding boxes are off by a few pixels, the viewer's text selection
behaves slightly strangely — you select word "ABC" and the highlight is
two pixels too far left — but search still works. This is why the SDK
exposes a `dpi=` argument: the higher the OCR DPI, the tighter the
alignment between the visible and invisible streams.

## Why fonts matter

PDF text is rendered with a real font. The overlay needs a font that
covers every codepoint the OCR engine produced, even though no glyph is
ever painted. On Latin documents, the default Helvetica-equivalent works
fine because every character is in basic ASCII. On CJK, Arabic, or
Cyrillic documents, you have to register a Unicode-capable font like
DejaVu Sans or Noto Sans, otherwise the PDF generator fails when it
tries to encode a codepoint the font does not cover.

The SDK auto-discovers a Unicode font on first use and registers it once
per process. If no usable font is found and the OCR text contains
non-Latin glyphs, the SDK raises
[`UnicodeFontRequired`][turboocr.UnicodeFontRequired] rather than
silently producing a corrupted text layer. See the
[handle non-Latin PDFs](../how-tos/handle_non_latin_pdfs.md) how-to for
the override knobs.

## Trade-offs

The overlay technique is forgiving but not free. Each output PDF is
slightly larger than its source because the text stream adds bytes, and
that overhead scales with the amount of recognized text. A two-page
invoice with about 70 OCR'd items typically grows by 15–20 kB. For
multi-megabyte scanned documents the relative overhead is negligible.

## Where to go next

- [Searchable PDF API](../api/searchable_pdf.md) — full signature and
  font-error hierarchy.
- [Handle non-Latin PDFs](../how-tos/handle_non_latin_pdfs.md) — recipe
  for the font-override path.

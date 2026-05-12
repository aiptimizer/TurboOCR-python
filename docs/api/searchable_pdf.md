# Searchable PDF

`Client.make_searchable_pdf(...)` returns a PDF with an invisible text layer
aligned to the original page geometry. The output is selectable, copyable, and
full-text-searchable in every PDF viewer / indexer.

For non-Latin scripts (CJK, Arabic, Cyrillic, …), the SDK auto-discovers a
Unicode font (`DejaVuSans` / `NotoSans` on Linux, Arial Unicode on macOS), or
takes an explicit `font_path=<.ttf>`. If non-Latin glyphs are present and no
Unicode font is found, the SDK raises `UnicodeFontRequired` rather than
silently producing a broken text layer.

The font registration step is thread-safe — multiple threads can call
`make_searchable_pdf` concurrently without racing on the global reportlab
font registry.

## `Client.make_searchable_pdf`

The high-level convenience method on the HTTP / async / gRPC clients —
see [Client.make_searchable_pdf][turboocr.Client.make_searchable_pdf] on the
[Clients](clients.md) page for the full signature.

## `turboocr.searchable_pdf` module

::: turboocr.searchable_pdf.make_searchable_pdf

::: turboocr.searchable_pdf.discover_unicode_font

## Font errors

::: turboocr.FontError

::: turboocr.UnicodeFontRequired

::: turboocr.FontGlyphMissing

# Handle non-Latin PDFs

Searchable-PDF output embeds an invisible text layer aligned to the
original page geometry. For non-Latin scripts (CJK, Arabic, Cyrillic, …)
that text layer needs a Unicode-capable font, otherwise the glyphs render
as boxes or get dropped.

!!! note

    OCR itself runs on the server. This page covers the *output* font for
    [`Client.make_searchable_pdf`][turboocr.Client.make_searchable_pdf],
    not the OCR engine's language settings.

## The auto-discovery path

On most Linux machines, DejaVu Sans or Noto Sans is already installed and
the SDK picks one up automatically:

```python
from pathlib import Path
from turboocr import Client

PDF = Path("examples/sample/acme_invoice.pdf")

client = Client(timeout=180.0)
overlay = client.make_searchable_pdf(PDF, dpi=200)
Path("/tmp/out.pdf").write_bytes(overlay)
```

If discovery fails on a non-Latin document, the SDK raises
[`UnicodeFontRequired`][turboocr.UnicodeFontRequired] rather than emitting
a broken text layer.

## Force a specific font

Pass `font_path=` with an absolute path to a `.ttf` or `.otf`:

```python
overlay = client.make_searchable_pdf(
    PDF,
    dpi=200,
    font_path="/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
)
```

## Set a default via environment

Same effect, no code change — useful in containers:

```bash
export TURBO_OCR_FONT=/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc
```

`font_path=` always wins over `TURBO_OCR_FONT` when both are set.

## Where to go next

- [Searchable PDF API](../api/searchable_pdf.md) — full signature and
  font-error hierarchy.
- [Searchable PDF internals](../explanation/searchable_pdf_internals.md) —
  how the invisible text overlay technique works.

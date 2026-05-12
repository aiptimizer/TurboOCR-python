# Markdown rendering

`render_to_markdown(...)` walks the reading order and maps each layout class to
a Markdown construct (`doc_title` → `# H1`, `display_formula` → `$$ ... $$`,
`table` → HTML or fenced block, etc.). The label-to-construct map is pluggable
via `MarkdownStyle`.

Two shorter forms are available too:

- `render_ocr_to_markdown(ocr_response)` — single image
- `render_pdf_to_markdown(pdf_response)` — multi-page PDF
- `Client.to_markdown(...)` — one-call convenience that does
  `recognize_image` (or `recognize_pdf`) + `render_to_markdown` in one step

`MarkdownDocument.structured()` returns the parsed tree (a list of
`MarkdownNode` objects) for programmatic inspection.

## `render_to_markdown`

::: turboocr.render_to_markdown

## `MarkdownStyle`

::: turboocr.MarkdownStyle

## `MarkdownDocument`

::: turboocr.MarkdownDocument

## `MarkdownNode`

::: turboocr.MarkdownNode

## `NodeKind`

::: turboocr.NodeKind

# Layout and reading order

The TurboOCR server returns three concentric views of the same page. They
sound similar but answer very different questions. Understanding the
difference is the single biggest lever you have for getting cleaner
downstream output.

## The three views

**Text items** are the raw OCR output. Each item is a single recognized
text region — typically a word or a short phrase — with its own bounding
box and confidence score. There is no notion of paragraphs or grouping
here; an invoice header and the page number both appear as text items at
the same level. This view is exhaustive but unstructured.

**Layout boxes** are the layout analyser's opinion about what *kind* of
region each part of the page is: `paragraph_title`, `text`, `table`,
`figure`, `display_formula`, and so on. A layout box describes geometry
and a class label, but it does *not* contain the OCR text. Layout boxes
tell you "this rectangle is a heading"; they leave it to text items to
tell you what the heading says.

**Blocks** are the join of the two: a single block ties one layout box
to all the text items that fall inside it, in a sensible reading order,
and exposes the resulting text as a single string on `block.content`. A
heading block contains the heading text. A paragraph block contains the
whole paragraph. A table block contains the row-major OCR'd cell text.
Blocks are the view almost every downstream consumer actually wants.

## What `reading_order` adds

The page's layout analyser also returns a `reading_order` — a permutation
that tells you which block comes first, which comes next, and so on. For
single-column documents this is mostly a top-to-bottom sort and you would
not miss much by sorting by `y`. The reading order earns its keep on
multi-column layouts, sidebars, and figure captions, where the natural
reading sequence does not follow the geometry. Multi-column scientific
papers are the classic case: column 1's text continues at the top of
column 2, not on the line directly to its right.

The Markdown renderer uses `reading_order` to walk blocks in document
order before emitting headings, paragraphs, and tables. If you request
`include_blocks=True` but not `reading_order=True`, you still get clean
blocks — they just come back in scan order, which may surprise you.

## When to use which

Most users want blocks. If you are building a Markdown pipeline, an LLM
ingestion step, or a "summarize this PDF" feature, the right call is
`recognize_pdf(..., layout=True, reading_order=True, include_blocks=True)`
and a loop over `response.text` or the rendered Markdown.

Drop down to raw text items when you need word-level geometry — for
example, drawing per-word boxes on top of the original image, or
building your own custom layout heuristics. The text items are the same
data the blocks were built from; you are just bypassing the grouping.

Layout boxes on their own are rarely useful in isolation. They are most
interesting as input to whatever the next layout-aware feature is.

## A note on tables and formulas

`Table.text` and `Formula.text` give you what the OCR engine actually
read, in row-major order. Structured shapes — `Table.html`, `Table.cells`,
`Formula.latex` — are reserved fields that the SDK exposes today and
that the server will populate when the table-structure and LaTeX-OCR
features ship. Your code can read them now and the values will simply
turn from `None` into real strings when the server starts emitting them,
with no SDK upgrade required.

## Where to go next

- [Layout & blocks API](../api/layout.md) — exact field shapes for
  `Block`, `LayoutBox`, `BoundingBox`, `TextItem`.
- [Markdown rendering API](../api/markdown.md) — how the renderer turns
  blocks into Markdown nodes.

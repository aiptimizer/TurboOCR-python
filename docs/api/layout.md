# Layout, blocks, geometry

## `Block`

Reading-order-grouped paragraph with bounding box, layout class, and content.
Emitted on the response when `include_blocks=True`.

::: turboocr.Block

## `TextItem`

A single recognised word/line with confidence and bounding box.

::: turboocr.TextItem

## `BoundingBox`

::: turboocr.BoundingBox

## `LayoutBox`

::: turboocr.LayoutBox

## `LayoutLabel`

::: turboocr.LayoutLabel

## `Table`

::: turboocr.Table

## `Formula`

::: turboocr.Formula

!!! info "Tables and formulas — partial support today"

    As of server v2.2.3, the server detects table and formula **regions** (you
    get a `bounding_box` and row-major OCR'd `text`) but does **not** emit
    cell structure or LaTeX source. `Table.html`, `Table.cells`, and
    `Formula.latex` are always `None`. The SDK is forward-compatible: when the
    server ships table-structure-recognition and LaTeX OCR, those fields will
    populate without any SDK code changes.

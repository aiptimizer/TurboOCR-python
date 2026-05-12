# Your first PDF → Markdown pipeline

By the end of this tutorial you will have installed `turboocr`, pointed it
at a running TurboOCR server, OCR'd a sample image, converted a real PDF
invoice to Markdown, and saved the result to disk. It takes about ten
minutes if the server is already running.

## What you need

- Python 3.12 or newer.
- A running TurboOCR server. Anywhere reachable over HTTP works; the
  default is `http://localhost:8000`.
- The bundled `acme_invoice.pdf` and `acme_invoice.png` fixtures (clone the
  repo or download them from
  [`examples/sample/`](https://github.com/aiptimizer/turboocr-python/tree/develop/examples/sample)).

This tutorial assumes the server is configured for **Latin** OCR, which is
the bundled default.

## Step 1 — Install the package

```bash
pip install turboocr
```

This pulls in the HTTP client, the CLI, and the searchable-PDF generator.
You do not need the `[grpc]` extra unless you specifically want gRPC; for
this tutorial, plain HTTP is enough.

Verify the install:

```python
import turboocr

print(turboocr.__version__)
```

## Step 2 — Connect to the server

Create a [`Client`][turboocr.Client]. With no arguments it reads
`TURBO_OCR_BASE_URL` from the environment, falling back to
`http://localhost:8000`:

```python
from turboocr import Client

client = Client()
print(client.base_url)
```

If your server lives somewhere else, pass it explicitly:

```python
client = Client(base_url="http://ocr.internal:8000", timeout=60.0)
```

Quick sanity check — ask the server if it is healthy:

```python
health = client.health()
print(f"ok={health.ok} status={health.status_code}")
```

A `True` and a `200` mean you are ready to OCR something.

## Step 3 — OCR your first image

Point the client at the sample PNG. The default response gives you a flat
list of text items, each with a bounding box and a confidence score:

```python
from pathlib import Path

from turboocr import Client

IMAGE = Path("examples/sample/acme_invoice.png")

client = Client()
response = client.recognize_image(IMAGE)

print(f"recognized {len(response.results)} text items")
for item in response.results[:3]:
    print(f"  {item.text!r} (conf={item.confidence:.2f})")
```

You should see roughly 71 items, starting with `'ACME Corporation'`.

## Step 4 — Move up to a PDF

PDFs are multi-page, so the response shape is slightly different — you get
a [`PdfResponse`][turboocr.PdfResponse] with a `.pages` list. Pass
`layout=True`, `reading_order=True`, and `include_blocks=True` so the
server returns the geometric structure we will need in the next step:

```python
PDF = Path("examples/sample/acme_invoice.pdf")

response = client.recognize_pdf(
    PDF,
    dpi=150,
    layout=True,
    reading_order=True,
    include_blocks=True,
)
print(f"pages={len(response.pages)}")
```

PDFs take longer than single images. The `Client(timeout=120.0)` argument
from earlier covers most invoices comfortably.

## Step 5 — Render to Markdown

[`render_to_markdown`][turboocr.render_to_markdown] walks the reading-order
blocks and turns them into a [`MarkdownDocument`][turboocr.MarkdownDocument]:

```python
from turboocr import render_to_markdown

doc = render_to_markdown(response)
print(f"chars={len(doc.markdown)}")
print(doc.markdown[:200])
```

## Step 6 — Save it

`MarkdownDocument.markdown` is a plain string, so writing it to disk is
one line:

```python
out = Path("/tmp/acme_invoice.md")
out.write_text(doc.markdown)
print(f"wrote {out}")
```

Open the file in any Markdown viewer — headings, paragraphs, and tables
all come through as readable Markdown.

## Where to go next

- For a recipe-shaped reminder of how to tweak retries, see
  [Configure retries](../how-tos/configure_retries.md).
- To scale this from one file to a whole folder, continue with
  [Tutorial 2 — async folder pipeline](02_async_folder_pipeline.md).
- For background on what `blocks` and `reading_order` actually mean, see
  [Layout & reading order](../explanation/layout_and_reading_order.md).

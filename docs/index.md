# turboocr

Typed Python client for the [TurboOCR](https://github.com/aiptimizer/TurboOCR)
server. Sync + async, HTTP + gRPC, layout-aware Markdown rendering,
searchable-PDF generation.

## Install

```bash
pip install turboocr             # HTTP + CLI + searchable-PDF
pip install 'turboocr[grpc]'     # add the gRPC transport
pip install 'turboocr[all]'      # everything optional
```

Requires Python 3.12+.

## Quickstart

```python
from turboocr import Client, render_to_markdown

with Client(base_url="http://localhost:8000") as client:
    img = client.recognize_image("page.png", layout=True, include_blocks=True)
    pdf = client.recognize_pdf("paper.pdf", dpi=150, include_blocks=True)
    markdown = render_to_markdown(pdf).markdown
```

For runnable end-to-end scripts (image OCR, PDF→Markdown, searchable PDFs,
async, gRPC, batch, retries, custom `httpx.Client`, hooks, Markdown styling,
folder pipelines), see the [examples](examples.md) — every script runs against
the bundled ACME invoice fixture.

## API at a glance

| Area | Entry points |
|------|--------------|
| [HTTP clients](api/clients.md) | `Client`, `AsyncClient` |
| [gRPC clients](api/grpc.md) | `GrpcClient`, `AsyncGrpcClient` |
| [Response models](api/models.md) | `OcrResponse`, `PdfResponse`, `BatchResponse`, `HealthStatus` |
| [Layout & blocks](api/layout.md) | `Block`, `BoundingBox`, `LayoutBox`, `LayoutLabel`, `TextItem`, `Table`, `Formula` |
| [Markdown rendering](api/markdown.md) | `render_to_markdown`, `MarkdownStyle`, `MarkdownDocument`, `NodeKind` |
| [Searchable PDF](api/searchable_pdf.md) | `Client.make_searchable_pdf`, `turboocr.searchable_pdf` |
| [Retries / timeouts / hooks](api/retry.md) | `RetryPolicy`, `on_request`, `on_response` |
| [Errors](api/errors.md) | `TurboOcrError` hierarchy, font errors |
| [CLI](api/cli.md) | `turbo-ocr` command |

## Server compatibility

`SERVER_API_VERSION_MIN` and `SERVER_API_VERSION_MAX_EXCLUSIVE` document the
supported range. Response models use `extra="allow"` so additive server
changes (e.g. a new `request_id` field) are preserved on `.model_extra`
instead of crashing on parse.

## Versioning

Names exported by `turboocr.__all__` are the public API. Underscored modules
(`_core`, `_http`, `_grpc`) are internal and may change at any time. Pre-1.0,
breaking changes are signalled by a minor-version bump; deprecated public APIs
emit `DeprecationWarning` and stay supported for at least one minor version
after deprecation.

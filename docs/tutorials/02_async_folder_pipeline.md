# Building an async folder-watcher pipeline

In [tutorial 1](01_first_pdf_to_markdown.md) you OCR'd one PDF and saved
the Markdown. Now we will scale that to a folder of PDFs, processed
concurrently with bounded parallelism. By the end you will have a small
pipeline you can drop into a real ingestion job.

## What you will build

- A coroutine that takes a single `Path` and writes the rendered Markdown
  next to it.
- A driver that scans a folder, fans out coroutines onto a shared
  [`AsyncClient`][turboocr.AsyncClient], and caps concurrency with an
  `asyncio.Semaphore` so you do not stampede the server.

## Step 1 — One file, asynchronously

Switch `Client` for [`AsyncClient`][turboocr.AsyncClient]. Same method
surface — every call is awaitable. Always use it as an `async with`
context manager so the underlying `httpx.AsyncClient` is closed:

```python
import asyncio
from pathlib import Path

from turboocr import AsyncClient, render_to_markdown


async def ocr_one(client: AsyncClient, pdf: Path, out_dir: Path) -> Path:
    response = await client.recognize_pdf(pdf, include_blocks=True)
    out = out_dir / pdf.with_suffix(".md").name
    out.write_text(render_to_markdown(response).markdown)
    return out
```

## Step 2 — Fan out with a semaphore

`asyncio.gather` will happily launch a hundred coroutines at once. That is
not what you want against a real OCR server — most servers have a finite
worker pool, and overloading them costs you tail latency, not throughput.
A semaphore is the simplest way to cap parallelism:

```python
async def bounded(sem: asyncio.Semaphore, coro):
    async with sem:
        return await coro
```

Pick a concurrency number that matches your server's worker count. Four
is a sensible default for a single-GPU server.

## Step 3 — Drive the folder

Glob the input directory, build one coroutine per file, and gather:

```python
async def process_folder(in_dir: Path, out_dir: Path, max_inflight: int = 4) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(in_dir.glob("*.pdf"))
    if not pdfs:
        print(f"no PDFs under {in_dir}")
        return

    sem = asyncio.Semaphore(max_inflight)
    async with AsyncClient(timeout=60.0) as client:
        tasks = [bounded(sem, ocr_one(client, pdf, out_dir)) for pdf in pdfs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for pdf, result in zip(pdfs, results, strict=True):
        if isinstance(result, Exception):
            print(f"FAIL {pdf.name}: {result!r}")
        else:
            print(f"ok   {result}")
```

`return_exceptions=True` is the important bit: without it, the first
failure cancels every sibling in flight. With it, a single bad PDF only
loses that one PDF and the others run to completion.

## Step 4 — Run it

```python
if __name__ == "__main__":
    asyncio.run(process_folder(
        in_dir=Path("examples/sample"),
        out_dir=Path("/tmp/turboocr-folder-pipeline"),
        max_inflight=4,
    ))
```

Drop the file into a folder, run it, and watch the Markdown appear under
`/tmp/turboocr-folder-pipeline/`. For a fixture-only run you will see one
output file; on a real folder of invoices, each PDF gets its own.

## Where to go next

- [Batch partial failures](../how-tos/batch_with_partial_failures.md) — if
  you prefer one HTTP call per group instead of one per file.
- [Custom `httpx.Client`](../how-tos/use_custom_httpx_client.md) — to set
  connection limits, mTLS, or a corporate proxy on the shared transport.
- [Configure retries](../how-tos/configure_retries.md) — to tighten the
  retry budget when running large batches.

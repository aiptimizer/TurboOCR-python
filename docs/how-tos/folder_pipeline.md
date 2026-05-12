# OCR a folder of PDFs concurrently

Standard recipe: scan a directory, OCR every PDF in parallel with
[`AsyncClient`][turboocr.AsyncClient], cap concurrency with an
`asyncio.Semaphore`, write Markdown next to each output.

```python
import asyncio
from pathlib import Path

from turboocr import AsyncClient, render_to_markdown


async def ocr_one(client: AsyncClient, pdf: Path, out_dir: Path) -> Path:
    response = await client.recognize_pdf(pdf, include_blocks=True)
    out = out_dir / pdf.with_suffix(".md").name
    out.write_text(render_to_markdown(response).markdown)
    return out


async def bounded(sem: asyncio.Semaphore, coro):
    async with sem:
        return await coro


async def process_folder(in_dir: Path, out_dir: Path, max_inflight: int = 32) -> None:
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


if __name__ == "__main__":
    asyncio.run(process_folder(
        in_dir=Path("examples/sample"),
        out_dir=Path("/tmp/turboocr-folder-pipeline"),
    ))
```

## Why the semaphore

`asyncio.gather` will happily launch every coroutine at once. Without a
cap you saturate the server's queue and inflate tail latency. The
semaphore bounds in-flight work to `max_inflight`.

## Pick a concurrency number

`max_inflight=32` is a reasonable starting point for the TurboOCR server
(it runs many concurrent OCR pipelines on the same GPU). Tune from there:

- Watch the server's `/healthz` or your own request-latency metric.
- If p99 latency climbs without throughput going up, lower the cap.
- If the server is bored (low CPU, low GPU utilisation) and your queue
  has work waiting, raise it.

The "right" number depends on PDF page counts, your GPU's batch size, and
how many other clients hit the same server. There is no single magic
value.

## Why `return_exceptions=True`

```python
results = await asyncio.gather(*tasks, return_exceptions=True)
```

Without it, the first failed coroutine cancels every sibling in flight.
With it, a single bad PDF only loses that one PDF; the others run to
completion and you log the failure separately.

## Where to go next

- [Batch partial failures](batch_with_partial_failures.md) — one HTTP
  call per group instead of one per file.
- [Custom `httpx.Client`](use_custom_httpx_client.md) — connection
  limits, mTLS, corporate proxy on the shared transport.
- [Configure retries](configure_retries.md) — tighten the retry budget
  when running large batches.

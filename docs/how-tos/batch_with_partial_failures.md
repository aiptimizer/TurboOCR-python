# Batch with partial failures

[`Client.recognize_batch`][turboocr.Client.recognize_batch] OCRs multiple
images in a single HTTP call. The server returns parallel
`batch_results` / `errors` lists — one slot per input. Some slots may
succeed and others may fail in the same response.

`BatchResponse.iter_results()` pairs the two lists into a tagged-union
list of [`BatchSuccess`][turboocr.BatchSuccess] /
[`BatchFailure`][turboocr.BatchFailure], so you can `match` on the kind
instead of zipping by hand:

```python
from pathlib import Path

from turboocr import BatchFailure, BatchSuccess, Client

IMAGES = [
    Path("examples/sample/acme_invoice.png"),
    Path("examples/sample/acme_invoice.png"),
    Path("examples/sample/acme_invoice.png"),
]

client = Client()
batch = client.recognize_batch(IMAGES, include_blocks=True)

for result in batch.iter_results():
    match result:
        case BatchSuccess(index=i, response=resp):
            print(f"[{i}] ok: {len(resp.results)} items")
        case BatchFailure(index=i, error=msg):
            print(f"[{i}] failed: {msg}")
```

The HTTP call itself succeeds even when individual items fail, so
partial-success is the normal case to plan for, not an edge case.

## Where to go next

- [API: BatchResponse](../api/models.md) — full field reference.
- [OCR a folder of PDFs concurrently](folder_pipeline.md) — when
  one-call-per-batch is the wrong shape and you want one call per file.

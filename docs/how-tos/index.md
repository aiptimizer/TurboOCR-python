# How-to guides

How-tos are problem-shaped recipes. Each one answers a single, narrowly
scoped question — "how do I do X?" — and assumes you already know the
basics. If you are new, work through the [tutorials](../tutorials/index.md)
first.

## Available recipes

- [Configure retries](configure_retries.md) — retry only on `503`, change
  backoff, respect `Retry-After`.
- [Handle non-Latin PDFs](handle_non_latin_pdfs.md) — pick the right
  Unicode font for searchable-PDF output via `font_path` or
  `TURBO_OCR_FONT`.
- [Use a custom `httpx.Client`](use_custom_httpx_client.md) — mTLS,
  proxies, connection limits, custom CA bundles.
- [Batch with partial failures](batch_with_partial_failures.md) — keep
  successful results when one item in a batch fails, using
  [`BatchResponse.iter_results`][turboocr.BatchResponse.iter_results].

For exhaustive parameter lists see the [API reference](../api/clients.md);
for conceptual background see [Explanation](../explanation/index.md).

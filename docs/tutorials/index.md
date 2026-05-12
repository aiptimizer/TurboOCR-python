# Tutorials

Tutorials are learning-oriented. They walk you through a complete, realistic
workflow end-to-end. If you have never used `turboocr` before, start here.

For look-up tables, signatures, and exhaustive parameter lists, see the
[API reference](../api/clients.md). For short problem-shaped recipes, see
[How-to guides](../how-tos/index.md). For background on *why* the SDK works
the way it does, see [Explanation](../explanation/index.md).

## Available tutorials

1. [Your first PDF → Markdown pipeline](01_first_pdf_to_markdown.md) —
   install the package, run the TurboOCR server, OCR your first image, then
   convert a real PDF invoice to Markdown and save it to disk. Beginner.
2. [Building an async folder-watcher pipeline](02_async_folder_pipeline.md) —
   take what you learned in tutorial 1 and scale it: drop PDFs into a folder
   and have them OCR'd concurrently with bounded parallelism. Intermediate.

Each tutorial uses the bundled `acme_invoice.pdf` / `acme_invoice.png`
fixtures from the [examples directory](https://github.com/aiptimizer/TurboOCR-python/tree/main/examples/sample),
so you can run every snippet against real data without finding your own
sample files.

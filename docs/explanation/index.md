# Explanation

These pages exist to give you a mental model. They are not tutorials and
they are not recipes — there are no commands to run, and nothing here is
load-bearing for getting a working OCR pipeline up. Read them when you
want to understand *why* the SDK is shaped the way it is.

## Topics

- [Layout and reading order](layout_and_reading_order.md) — what a
  "block" is, how `reading_order` differs from `layout`, and why the
  Markdown renderer leans on blocks rather than raw OCR items.
- [Searchable PDF internals](searchable_pdf_internals.md) — the
  invisible-text-overlay technique, why it preserves the original page,
  and where the font requirement comes from.
- [HTTP vs gRPC](http_vs_grpc.md) — when each transport is the right
  pick, and the proto3 bool-presence caveat that subtly affects gRPC
  defaults.

## Where to go next

- For step-by-step walkthroughs, see the [tutorials](../tutorials/index.md).
- For short answers to specific problems, see the
  [how-to guides](../how-tos/index.md).
- For exhaustive signatures, see the [API reference](../api/clients.md).

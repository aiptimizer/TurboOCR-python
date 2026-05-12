# gRPC clients

`GrpcClient` and `AsyncGrpcClient` mirror the HTTP clients over gRPC.
Requires `pip install 'turboocr[grpc]'`.

!!! warning "Two parity caveats"

    - The gRPC proto's bool fields lack field presence (proto3 without
      `optional`), so `None` is sent as `False`. Today the server defaults all
      bool options to `False`, so behavior matches the HTTP client — if the
      server ever flips a default, gRPC users would have to opt in explicitly.
    - `GrpcClient.recognize_pdf(reading_order=True)` raises
      `InvalidParameter` — the proto lacks the `reading_order` field. Use the
      HTTP client for PDFs that need reading order.

## `GrpcClient`

::: turboocr.GrpcClient

## `AsyncGrpcClient`

::: turboocr.AsyncGrpcClient

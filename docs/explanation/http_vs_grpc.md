# HTTP vs gRPC

The SDK ships two transports for the same API surface:
[`Client`][turboocr.Client] / [`AsyncClient`][turboocr.AsyncClient] over
HTTP, and `GrpcClient` / `AsyncGrpcClient` over gRPC. Both speak to the
same server. Which one you pick is a deployment question, not a features
or speed question — for an OCR workload, GPU inference dominates the
wall time, so the wire format barely shows up in the budget.

## Pick HTTP unless you have a specific reason not to

It is the default. It works through every proxy and observability tool
you already have. It is the only transport that supports
`recognize_pdf(reading_order=True)` today — the gRPC schema lacks the
field, so the gRPC client raises
[`InvalidParameter`][turboocr.InvalidParameter]. Custom transports
(mTLS, proxies, connection limits) come for free because you can pass
your own `httpx.Client`.

## Pick gRPC if you specifically want…

- A strict, generated-from-proto wire contract instead of negotiating
  JSON shape changes.
- Native bidirectional streaming for some future server-side feature
  (the proto is set up for it; today's RPCs are unary).
- Tight integration with an existing gRPC-only infrastructure you
  already operate.

## The proto3 bool-presence caveat

Protobuf 3 bool fields without `optional` cannot distinguish "unset"
from "explicitly `False`". The TurboOCR proto's bool options
(`layout`, `include_blocks`, …) are written that way, so a `None` from
Python is encoded as `False` on the wire.

The HTTP client treats `None` as "omit this field; use the server's
default". The gRPC client cannot — `None` becomes a hard `False`. Today
the server defaults every bool option to `False`, so behaviour matches.
If the server ever flips a default to `True`, HTTP clients pick it up
automatically; gRPC users would have to opt in explicitly.

## Where to go next

- [HTTP clients API](../api/clients.md) — `Client`, `AsyncClient`.
- [gRPC clients API](../api/grpc.md) — `GrpcClient`, `AsyncGrpcClient`
  and the documented parity caveats.

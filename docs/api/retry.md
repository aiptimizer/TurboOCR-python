# Retries, timeouts, hooks

## `RetryPolicy`

Defaults retry HTTP `{429, 502, 503, 504}` (and gRPC
`{UNAVAILABLE, DEADLINE_EXCEEDED, RESOURCE_EXHAUSTED}`) up to 3 times with
exponential backoff + jitter. `Retry-After` is honoured.

::: turboocr.RetryPolicy

## Timeouts

Two layers:

- **Client-wide**: `Client(timeout=30.0, ...)` sets the per-request default.
- **Per-call**: `client.recognize_image("page.png", timeout=15.0)` overrides
  the default for that single call. A per-call `timeout=None` means "no
  per-call override — use the client default".

For finer control, pass a pre-built `httpx.Timeout` via `http_client=`:

```python
import httpx
from turboocr import Client

http = httpx.Client(
    base_url="http://localhost:8000",
    timeout=httpx.Timeout(connect=2.0, read=60.0, write=60.0, pool=30.0),
)
client = Client(http_client=http)
```

## Hooks

`on_request` / `on_response` are httpx event hooks invoked around every
request. Use them for OpenTelemetry spans, request counters, or simple stdout
tracing.

```python
import httpx
from turboocr import Client

def on_request(request: httpx.Request) -> None:
    print(f"-> {request.method} {request.url.path}")

def on_response(response: httpx.Response) -> None:
    print(f"<- {response.status_code} {response.request.url.path}")

client = Client(on_request=on_request, on_response=on_response)
```

See [`docs/12_hooks_and_logging.py`](../examples.md#12-hooks-and-logging) for
a runnable version.

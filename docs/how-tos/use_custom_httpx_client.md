# Use a custom `httpx.Client`

Pass `http_client=` to take full control of the transport — useful for
mTLS, corporate proxies, custom CA bundles, or fine-grained connection
limits.

```python
from pathlib import Path

import httpx

from turboocr import Client

http = httpx.Client(
    base_url="http://localhost:8000",
    timeout=httpx.Timeout(connect=2.0, read=60.0, write=60.0, pool=30.0),
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
    headers={"X-Trace-Source": "ingest-prod"},
    # verify="/etc/ssl/corp-ca.pem",                       # custom CA
    # cert=("/etc/ssl/client.crt", "/etc/ssl/client.key"), # mTLS
    # proxy="http://proxy.corp.example:3128",              # forward proxy
)

client = Client(http_client=http)
response = client.recognize_image(Path("examples/sample/acme_invoice.png"))
print(f"{len(response.results)} items via shared httpx.Client")
```

A few rules:

- When you pass `http_client=`, the SDK does **not** own its lifecycle.
  Close it yourself (`http.close()` or `with httpx.Client(...) as http:`)
  when you are done.
- `base_url` on the `httpx.Client` and `base_url=` on `Client` must not
  disagree. If both are set, the `httpx.Client` value wins because it is
  applied at the transport layer.
- For async, do the same with `httpx.AsyncClient` and
  [`AsyncClient`][turboocr.AsyncClient].

## Where to go next

- [API: HTTP clients](../api/clients.md) — full constructor signature.
- [Configure retries](configure_retries.md) — retries layer on top of the
  custom transport without further configuration.

# Configure retries

The SDK's default [`RetryPolicy`][turboocr.RetryPolicy] retries on `429`,
`502`, `503`, and `504`. To narrow that to a single status code, or to
change the backoff curve, build a `RetryPolicy` and pass it to the client.

## Retry only on `503`

```python
from turboocr import Client, RetryPolicy

policy = RetryPolicy(
    attempts=5,
    backoff=0.5,
    backoff_cap=4.0,
    retry_statuses=frozenset({503}),
)

client = Client(retry=policy, timeout=30.0)
```

`attempts` is the **total** number of tries, not extra tries after the
first. `attempts=5` means at most four retries.

## Tune backoff

The delay between attempts is `min(backoff_cap, backoff * 2**(attempt-1))`
plus uniform jitter in `[0, jitter)`. With the values above the sequence
caps out at 4.0 s once `backoff * 2**(n-1)` exceeds the cap.

## Respect `Retry-After`

`respect_retry_after=True` (the default) means a server `Retry-After`
header overrides the computed backoff when it is longer. Set it to
`False` if your server emits unreasonably long values.

## Where to go next

- [API: RetryPolicy](../api/retry.md) — full field reference.
- [HTTP vs gRPC](../explanation/http_vs_grpc.md) — gRPC has its own
  default retry status set; the same `RetryPolicy` covers both.

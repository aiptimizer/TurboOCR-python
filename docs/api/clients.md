# HTTP clients

`Client` and `AsyncClient` share an identical method surface — anything you
can do with one, you can `await` with the other.

Construct either directly with `base_url`, from env vars with
`Client.from_env()`, or pass a pre-built `httpx.Client` via `http_client=`.
The introspection properties (`.base_url`, `.auth_scheme`, `.default_headers`,
`.timeout`, `.retry`) read back the resolved config.

## `Client`

::: turboocr.Client

## `AsyncClient`

::: turboocr.AsyncClient

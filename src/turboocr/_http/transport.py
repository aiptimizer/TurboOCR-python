from __future__ import annotations

import base64
from typing import Any, Final

import httpx

from ..errors import APIConnectionError, NetworkError, ProtocolError, Timeout, raise_for_error


def classify_httpx_error(exc: httpx.HTTPError) -> APIConnectionError:
    msg = f"{type(exc).__name__}: {exc}"
    if isinstance(exc, httpx.TimeoutException):
        return Timeout(msg)
    if isinstance(exc, httpx.RemoteProtocolError):
        return ProtocolError(msg)
    return NetworkError(msg)


_BODY_SNIPPET_MAX: Final[int] = 512


def parse_response(response: httpx.Response) -> dict[str, Any]:
    raw_body = response.text
    try:
        decoded = response.json()
    except ValueError as exc:
        if response.is_error:
            raise_for_error(
                status_code=response.status_code,
                code=None,
                message=f"{raw_body[:_BODY_SNIPPET_MAX]} (HTTP {response.status_code})",
                payload=None,
            )
        raise ProtocolError(
            f"server returned non-JSON success body "
            f"({raw_body[:_BODY_SNIPPET_MAX]!r}) at HTTP {response.status_code}",
            status_code=response.status_code,
        ) from exc

    payload: dict[str, Any] | None = decoded if isinstance(decoded, dict) else None

    if response.is_error:
        code = payload.get("error_code") if payload else None
        message = (payload.get("error") or payload.get("message")) if payload else None
        raise_for_error(
            status_code=response.status_code,
            code=code if isinstance(code, str) else None,
            message=message or raw_body[:_BODY_SNIPPET_MAX] or f"HTTP {response.status_code}",
            payload=payload,
        )

    if payload is None:
        raise ProtocolError(
            f"server returned non-object JSON ({type(decoded).__name__}): "
            f"{raw_body[:_BODY_SNIPPET_MAX]!r}",
            status_code=response.status_code,
        )
    return payload


def encode_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")

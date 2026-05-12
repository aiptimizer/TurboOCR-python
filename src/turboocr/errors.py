from __future__ import annotations

from typing import Any, Final


class TurboOcrError(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.payload = payload or {}


class APIConnectionError(TurboOcrError):
    pass


class Timeout(APIConnectionError):
    pass


class NetworkError(APIConnectionError):
    pass


class ProtocolError(APIConnectionError):
    pass


class InvalidParameter(TurboOcrError):
    pass


class LayoutDisabled(TurboOcrError):
    pass


class ImageDecodeError(TurboOcrError):
    pass


class DimensionsTooLarge(TurboOcrError):
    pass


class PoolExhausted(TurboOcrError):
    pass


class PdfRenderError(TurboOcrError):
    pass


class EmptyBody(TurboOcrError):
    pass


class ServerError(TurboOcrError):
    pass


_CODE_TO_EXC: Final[dict[str, type[TurboOcrError]]] = {
    "INVALID_PARAMETER": InvalidParameter,
    "INVALID_JSON": InvalidParameter,
    "INVALID_HEADER": InvalidParameter,
    "INVALID_DIMENSIONS": InvalidParameter,
    "INVALID_DPI": InvalidParameter,
    "INVALID_MULTIPART": InvalidParameter,
    "MISSING_HEADER": InvalidParameter,
    "MISSING_IMAGE": InvalidParameter,
    "MISSING_FILE": InvalidParameter,
    "MISSING_PDF": InvalidParameter,
    "EMPTY_BODY": EmptyBody,
    "EMPTY_BATCH": EmptyBody,
    "EMPTY_PDF": EmptyBody,
    "LAYOUT_DISABLED": LayoutDisabled,
    "IMAGE_DECODE_FAILED": ImageDecodeError,
    "BASE64_DECODE_FAILED": ImageDecodeError,
    "DIMENSIONS_TOO_LARGE": DimensionsTooLarge,
    "PDF_TOO_LARGE": DimensionsTooLarge,
    "BODY_SIZE_MISMATCH": InvalidParameter,
    "PDF_RENDER_FAILED": PdfRenderError,
    "NOT_READY": ServerError,
}


def raise_for_error(
    *,
    status_code: int,
    code: str | None,
    message: str,
    payload: dict[str, Any] | None = None,
) -> None:
    if 200 <= status_code < 300:
        return
    if "Server at capacity" in message:
        raise PoolExhausted(message, code=code, status_code=status_code, payload=payload)
    exc_cls = _CODE_TO_EXC.get(code or "", ServerError)
    raise exc_cls(message, code=code, status_code=status_code, payload=payload)

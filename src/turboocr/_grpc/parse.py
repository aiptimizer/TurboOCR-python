"""Parse gRPC response messages into the SDK's pydantic models.

``OCRResponse.json_response`` carries the identical bytes of the HTTP JSON
body the same server would emit on the HTTP path. When populated we feed
it straight to ``OcrResponse.model_validate_json`` — same validation, same
shape, zero field-by-field copying. The structural fallback runs only
when ``json_response`` is empty (test servers / stripped mocks).
"""

from __future__ import annotations

from ..models import (
    BatchResponse,
    BoundingBox,
    OcrResponse,
    PdfMode,
    PdfPage,
    PdfResponse,
    TextItem,
)
from ._stubs import ocr_pb2 as pb2


def _quad_from_bbox(bboxes: list[pb2.BoundingBox]) -> tuple[
    tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]
]:
    if not bboxes:
        return ((0, 0), (0, 0), (0, 0), (0, 0))
    bb = bboxes[0]
    xs = list(bb.x)
    ys = list(bb.y)
    pts = list(zip(xs, ys, strict=False))
    while len(pts) < 4:
        pts.append((0.0, 0.0))
    quad = tuple((int(x), int(y)) for x, y in pts[:4])
    return quad  # type: ignore[return-value]


def _ocr_response_from_results(resp: pb2.OCRResponse) -> OcrResponse:
    items: list[TextItem] = []
    for r in resp.results:
        items.append(
            TextItem(
                text=r.text,
                confidence=float(r.confidence),
                bounding_box=BoundingBox(points=_quad_from_bbox(list(r.bounding_box))),
            )
        )
    return OcrResponse(
        results=items,
        layout=[],
        reading_order=list(resp.reading_order),
        blocks=[],
    )


def parse_ocr_response(resp: pb2.OCRResponse) -> OcrResponse:
    if resp.json_response:
        return OcrResponse.model_validate_json(resp.json_response)
    return _ocr_response_from_results(resp)


def parse_batch_response(resp: pb2.OCRBatchResponse) -> BatchResponse:
    pages = [parse_ocr_response(r) for r in resp.batch_results]
    return BatchResponse(batch_results=pages, errors=[None] * len(pages))


def _pdf_page_from_proto(page: pb2.OCRPageResult, index: int) -> PdfPage:
    if page.json_response:
        # Per-page JSON: identical to the HTTP `/ocr/pdf` page entry.
        return PdfPage.model_validate_json(page.json_response)
    items: list[TextItem] = []
    for r in page.results:
        items.append(
            TextItem(
                text=r.text,
                confidence=float(r.confidence),
                bounding_box=BoundingBox(points=_quad_from_bbox(list(r.bounding_box))),
            )
        )
    mode_value = page.mode or PdfMode.ocr.value
    return PdfPage(
        page=page.page_number,
        page_index=index,
        dpi=page.dpi,
        width=page.width,
        height=page.height,
        results=items,
        mode=PdfMode(mode_value),
        text_layer_quality=page.text_layer_quality or "absent",
    )


def parse_pdf_response(resp: pb2.OCRPDFResponse) -> PdfResponse:
    pages = [_pdf_page_from_proto(p, i) for i, p in enumerate(resp.pages)]
    return PdfResponse(pages=pages)

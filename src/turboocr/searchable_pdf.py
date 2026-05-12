from __future__ import annotations

import logging
import os
import threading
from collections.abc import Iterable
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Final, Protocol

import pypdf
from reportlab.pdfgen import canvas as rl_canvas

from .errors import ProtocolError
from .models import OcrResponse, PdfPage, PdfResponse, TextItem

if TYPE_CHECKING:
    from reportlab.pdfgen.canvas import Canvas


logger = logging.getLogger("turboocr.searchable_pdf")

PDF_POINTS_PER_INCH: Final[float] = 72.0
INVISIBLE_TEXT_MODE: Final[int] = 3
DEFAULT_FONT_NAME: Final[str] = "TurboOcrUnicode"
BUILTIN_LATIN_FONT: Final[str] = "Helvetica"

_FONT_SEARCH_PATHS: Final[tuple[str, ...]] = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/google-noto/NotoSans-Regular.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "C:/Windows/Fonts/arial.ttf",
)


class FontResolver(Protocol):
    def __call__(self, sample_text: str) -> str: ...


@dataclass(frozen=True, slots=True)
class _OverlayPage:
    width_pt: float
    height_pt: float
    dpi: int
    items: list[TextItem]


def discover_unicode_font(extra_paths: Iterable[str] = ()) -> str | None:
    env_path = os.environ.get("TURBO_OCR_FONT")
    candidates: list[str] = []
    if env_path:
        candidates.append(env_path)
    candidates.extend(extra_paths)
    candidates.extend(_FONT_SEARCH_PATHS)
    for path in candidates:
        if Path(path).is_file():
            return path
    return None


# reportlab's pdfmetrics holds a process-wide global font registry. Two
# threads calling make_searchable_pdf concurrently could race on the
# check-then-register, double-registering or partially observing the new
# font. This lock serialises the check + registerFont pair.
_FONT_REGISTRATION_LOCK: Final[threading.Lock] = threading.Lock()


def _register_font(font_path: str) -> str:
    # Deferred: pdfbase/ttfonts only loads when non-Latin scripts force
    # custom-font registration, sparing the import cost for Latin-only callers.
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    with _FONT_REGISTRATION_LOCK:
        if DEFAULT_FONT_NAME not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(DEFAULT_FONT_NAME, font_path))
    return DEFAULT_FONT_NAME


def _needs_unicode(items: list[TextItem]) -> bool:
    return any(any(ord(c) > 127 for c in item.text) for item in items)


class FontError(RuntimeError):
    pass


class UnicodeFontRequired(FontError):
    pass


class FontGlyphMissing(FontError):
    pass


def _resolve_font(items_per_page: list[list[TextItem]], font_path: str | None) -> str:
    if font_path:
        return _register_font(font_path)
    if not any(_needs_unicode(p) for p in items_per_page):
        return BUILTIN_LATIN_FONT
    discovered = discover_unicode_font()
    if discovered:
        logger.debug("turbo-ocr searchable_pdf using font %s", discovered)
        return _register_font(discovered)
    raise UnicodeFontRequired(
        "non-Latin text detected but no Unicode font found; "
        "pass font_path=<.ttf> or set TURBO_OCR_FONT"
    )


def _draw_invisible_item(
    canvas: Canvas, item: TextItem, *, font_name: str, dpi: int, page_height_pt: float
) -> None:
    if not item.text.strip():
        logger.debug("skipping whitespace-only OCR item id=%s", item.id)
        return
    x0, y0, x1, y1 = item.bounding_box.aabb
    box_w_pt = _px_to_pt(x1 - x0, dpi)
    box_h_pt = _px_to_pt(y1 - y0, dpi)
    if box_w_pt <= 0 or box_h_pt <= 0:
        raise ProtocolError(
            f"degenerate bbox {item.bounding_box.aabb} for OCR item id={item.id}"
        )

    text_pt_x = _px_to_pt(x0, dpi)
    text_pt_y = page_height_pt - _px_to_pt(y1, dpi)
    font_size = max(1.0, box_h_pt * 0.9)
    canvas.setFont(font_name, font_size)
    text_width = canvas.stringWidth(item.text, font_name, font_size)
    if text_width <= 0:
        raise FontGlyphMissing(
            f"font {font_name!r} cannot render OCR item id={item.id} (text={item.text!r}); "
            "pass font_path=<.ttf supporting these scripts> or set TURBO_OCR_FONT"
        )

    canvas.saveState()
    canvas.translate(text_pt_x, text_pt_y)
    canvas.scale(box_w_pt / text_width, 1.0)
    text_obj = canvas.beginText(0, 0)
    text_obj.setTextRenderMode(INVISIBLE_TEXT_MODE)
    text_obj.textOut(item.text)
    canvas.drawText(text_obj)
    canvas.restoreState()


def _px_to_pt(px: float, dpi: int) -> float:
    return px * PDF_POINTS_PER_INCH / dpi


def _build_overlay_pdf(pages: list[_OverlayPage], font_name: str) -> bytes:
    buffer = BytesIO()
    pdf = rl_canvas.Canvas(buffer)
    for page in pages:
        pdf.setPageSize((page.width_pt, page.height_pt))
        for item in page.items:
            _draw_invisible_item(
                pdf, item, font_name=font_name, dpi=page.dpi, page_height_pt=page.height_pt
            )
        pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def _items_for_page(page: PdfPage) -> list[TextItem]:
    """Order a page's text items by reading_order, falling back to natural order.

    Validates that reading_order is a complete permutation of result indices
    (every index present exactly once). On any drift — out-of-range index,
    duplicate, or missing index — logs a warning and returns the unordered
    `page.results` list. Silently using a partial reading_order would lose or
    duplicate text in the invisible PDF layer.
    """
    if not page.reading_order:
        return list(page.results)
    n = len(page.results)
    if sorted(page.reading_order) != list(range(n)):
        logger.warning(
            "page %d reading_order is not a permutation of results "
            "(len=%d, results=%d) — falling back to natural order to avoid "
            "lost/duplicated text",
            page.page, len(page.reading_order), n,
        )
        return list(page.results)
    return [page.results[i] for i in page.reading_order]


def _coerce_to_pdf_response(
    response: PdfResponse | OcrResponse,
    *,
    dpi: int | None,
    page_width_pt: float | None = None,
    page_height_pt: float | None = None,
) -> PdfResponse:
    if isinstance(response, PdfResponse):
        return response
    if dpi is None:
        raise ValueError("dpi must be provided when overlaying an OcrResponse")
    # Pixel dimensions at the rendered DPI. When called from make_searchable_pdf
    # we pass the source PDF's mediabox so introspection of page.width/height
    # returns truthful values; when called standalone we fall back to 0 — the
    # overlay loop uses mediabox directly and doesn't read these fields.
    width_px = int(page_width_pt * dpi / PDF_POINTS_PER_INCH) if page_width_pt else 0
    height_px = int(page_height_pt * dpi / PDF_POINTS_PER_INCH) if page_height_pt else 0
    return PdfResponse(
        pages=[
            PdfPage(
                page=1,
                page_index=0,
                dpi=dpi,
                width=width_px,
                height=height_px,
                results=response.results,
                layout=response.layout,
                reading_order=response.reading_order,
                blocks=response.blocks,
                mode="ocr",  # type: ignore[arg-type]
                text_layer_quality="ocr",
            )
        ]
    )


def make_searchable_pdf(
    original_pdf: bytes,
    response: PdfResponse | OcrResponse,
    *,
    dpi: int | None = None,
    font_path: str | None = None,
) -> bytes:
    reader = pypdf.PdfReader(BytesIO(original_pdf))
    if isinstance(response, OcrResponse) and reader.pages:
        media = reader.pages[0].mediabox
        pdf_response = _coerce_to_pdf_response(
            response, dpi=dpi,
            page_width_pt=float(media.width),
            page_height_pt=float(media.height),
        )
    else:
        pdf_response = _coerce_to_pdf_response(response, dpi=dpi)
    if len(reader.pages) != len(pdf_response.pages):
        hint = ""
        if isinstance(response, OcrResponse) and len(reader.pages) > 1:
            hint = (
                " — you passed an OcrResponse (single-image OCR) for a "
                "multi-page PDF; call client.recognize_pdf() to get a "
                "PdfResponse instead"
            )
        raise ValueError(
            f"PDF has {len(reader.pages)} pages but OCR response has "
            f"{len(pdf_response.pages)}{hint}"
        )

    items_per_page = [_items_for_page(p) for p in pdf_response.pages]
    font_name = _resolve_font(items_per_page, font_path)

    overlay_pages: list[_OverlayPage] = []
    for original_page, ocr_page, items in zip(
        reader.pages, pdf_response.pages, items_per_page, strict=True
    ):
        media = original_page.mediabox
        overlay_pages.append(
            _OverlayPage(
                width_pt=float(media.width),
                height_pt=float(media.height),
                dpi=ocr_page.dpi,
                items=items,
            )
        )

    overlay_bytes = _build_overlay_pdf(overlay_pages, font_name)
    overlay_reader = pypdf.PdfReader(BytesIO(overlay_bytes))
    writer = pypdf.PdfWriter(clone_from=reader)
    for writer_page, overlay_page in zip(writer.pages, overlay_reader.pages, strict=True):
        writer_page.merge_page(overlay_page)

    out = BytesIO()
    writer.write(out)
    return out.getvalue()

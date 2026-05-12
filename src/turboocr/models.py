from __future__ import annotations

from enum import StrEnum
from functools import cached_property
from typing import Annotated, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_serializer

type Point = tuple[int, int]
type Quad = tuple[Point, Point, Point, Point]


class LayoutLabel(StrEnum):
    abstract = "abstract"
    algorithm = "algorithm"
    aside_text = "aside_text"
    chart = "chart"
    content = "content"
    display_formula = "display_formula"
    doc_title = "doc_title"
    figure_title = "figure_title"
    footer = "footer"
    footer_image = "footer_image"
    footnote = "footnote"
    formula_number = "formula_number"
    header = "header"
    header_image = "header_image"
    image = "image"
    inline_formula = "inline_formula"
    number = "number"
    paragraph_title = "paragraph_title"
    reference = "reference"
    reference_content = "reference_content"
    seal = "seal"
    table = "table"
    text = "text"
    vertical_text = "vertical_text"
    vision_footnote = "vision_footnote"
    supplementary_region = "SupplementaryRegion"


class PdfMode(StrEnum):
    ocr = "ocr"
    text = "text"
    auto = "auto"
    auto_verified = "auto_verified"
    geometric = "geometric"


# extra="allow" preserves new server fields on .model_extra so an additive
# server change (e.g. a new "request_id" key) parses cleanly without code
# changes here. A *rename* of a required field still raises
# ValidationError because all required fields have no default — only
# conditionally-emitted fields (layout / reading_order / blocks) carry
# default_factory=list, matching the server's "omit when not requested"
# contract.
class _Frozen(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="allow",
        populate_by_name=True,
        validate_assignment=False,
        ser_json_inf_nan="constants",
    )


class BoundingBox(_Frozen):
    points: Annotated[Quad, Field(description="4-corner polygon")]

    @field_validator("points", mode="before")
    @classmethod
    def _coerce(cls, v: object) -> object:
        if isinstance(v, list):
            return tuple((int(p[0]), int(p[1])) for p in v)
        return v

    @model_serializer
    def _serialize(self) -> list[list[int]]:
        # Match the server wire format: `[[x,y],[x,y],[x,y],[x,y]]`.
        return [list(p) for p in self.points]

    @cached_property
    def aabb(self) -> tuple[int, int, int, int]:
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return (min(xs), min(ys), max(xs), max(ys))

    @cached_property
    def center(self) -> Point:
        x0, y0, x1, y1 = self.aabb
        return ((x0 + x1) // 2, (y0 + y1) // 2)

    @cached_property
    def width(self) -> int:
        x0, _, x1, _ = self.aabb
        return x1 - x0

    @cached_property
    def height(self) -> int:
        _, y0, _, y1 = self.aabb
        return y1 - y0


class TextItem(_Frozen):
    text: str
    confidence: float
    bounding_box: BoundingBox
    id: int | None = None
    layout_id: int | None = None
    source: Literal["ocr", "pdf", "geometric", "auto", "auto_verified"] | None = None

    @field_validator("bounding_box", mode="before")
    @classmethod
    def _wrap_bbox(cls, v: object) -> object:
        if isinstance(v, list):
            return {"points": v}
        return v


class LayoutBox(_Frozen):
    class_name: Annotated[str, Field(alias="class")]
    class_id: int
    confidence: float
    bounding_box: BoundingBox
    id: int | None = None

    @field_validator("bounding_box", mode="before")
    @classmethod
    def _wrap_bbox(cls, v: object) -> object:
        if isinstance(v, list):
            return {"points": v}
        return v


class Block(_Frozen):
    id: int
    layout_id: int
    class_name: Annotated[str, Field(alias="class")]
    bounding_box: BoundingBox
    content: str
    order_index: int

    @field_validator("bounding_box", mode="before")
    @classmethod
    def _wrap_bbox(cls, v: object) -> object:
        if isinstance(v, list):
            return {"points": v}
        return v


_TABLE_LABELS: Final[frozenset[str]] = frozenset({LayoutLabel.table.value})
_FORMULA_LABELS: Final[frozenset[str]] = frozenset(
    {
        LayoutLabel.display_formula.value,
        LayoutLabel.formula_number.value,
        LayoutLabel.inline_formula.value,
    }
)


class Table(_Frozen):
    id: int
    bounding_box: BoundingBox
    text: str
    html: str | None = None
    cells: list[list[str]] | None = None


class Formula(_Frozen):
    id: int
    bounding_box: BoundingBox
    text: str
    is_inline: bool = False
    latex: str | None = None


def _synthesize_tables(blocks: list[Block]) -> list[Table]:
    return [
        Table(id=b.id, bounding_box=b.bounding_box, text=b.content)
        for b in blocks
        if b.class_name in _TABLE_LABELS
    ]


def _synthesize_formulas(blocks: list[Block]) -> list[Formula]:
    return [
        Formula(
            id=b.id,
            bounding_box=b.bounding_box,
            text=b.content,
            is_inline=b.class_name == LayoutLabel.inline_formula.value,
        )
        for b in blocks
        if b.class_name in _FORMULA_LABELS
    ]


class OcrResponse(_Frozen):
    """Single-image OCR result returned by `recognize_image` / `recognize_pixels`.

    Attributes:
        results: Token-level text items in detection order. Always
            populated.
        layout: Region boxes (titles, paragraphs, tables, figures, …).
            Populated only when the call was made with `layout=True`;
            empty list otherwise.
        reading_order: Indices into `results` giving human reading order.
            Populated only when `reading_order=True` was requested.
        blocks: Paragraph-level groupings with their own reading order.
            Populated only when `include_blocks=True` was requested.
        text: Cached property — the full text joined in reading order
            (blocks > reading_order > raw `results`).
        tables: Computed view of `blocks` filtered to table-like labels.
        formulas: Computed view of `blocks` filtered to formula-like
            labels (display, numbered, and inline).
    """

    results: list[TextItem]
    layout: list[LayoutBox] = Field(default_factory=list)
    reading_order: list[int] = Field(default_factory=list)
    blocks: list[Block] = Field(default_factory=list)

    @cached_property
    def text(self) -> str:
        if self.blocks:
            return "\n\n".join(b.content for b in self.blocks)
        if self.reading_order:
            return "\n".join(self.results[i].text for i in self.reading_order)
        return "\n".join(r.text for r in self.results)

    # Synthesized today from blocks where class is table/display_formula/etc.
    # When the server adds first-class `tables` / `formulas` JSON fields
    # (TableSR + LaTeX OCR), flip these to regular Field(default_factory=list)
    # and add a model_validator that synthesizes only when the server omits
    # them. User code (`for t in resp.tables`) keeps working unchanged.
    @computed_field  # type: ignore[prop-decorator]
    @property
    def tables(self) -> list[Table]:
        return _synthesize_tables(self.blocks)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def formulas(self) -> list[Formula]:
        return _synthesize_formulas(self.blocks)


class BatchSuccess(_Frozen):
    index: int
    response: OcrResponse


class BatchFailure(_Frozen):
    index: int
    error: str


type BatchResult = BatchSuccess | BatchFailure


class BatchResponse(_Frozen):
    """Multi-image OCR result returned by `recognize_batch`.

    `batch_results` and `errors` are *parallel* lists of equal length:
    slot `i` is either a valid [`OcrResponse`][turboocr.OcrResponse] with
    `errors[i] is None`, or a failure where `errors[i]` carries the
    server's error message and `batch_results[i]` is an empty placeholder
    `OcrResponse(results=[])`. Per-slot failures never raise — they land
    in `errors` so one bad input cannot fail the whole batch.

    Prefer [`iter_results`][turboocr.BatchResponse.iter_results] for a
    tagged-union iteration instead of zipping the two lists manually.

    Attributes:
        batch_results: One `OcrResponse` per input, in submission order.
        errors: Parallel `str | None` list — `None` for successes, the
            server's error message otherwise.
    """

    batch_results: list[OcrResponse]
    errors: list[str | None]

    def iter_results(self) -> list[BatchResult]:
        """Pair `batch_results` and `errors` into a tagged-union list.

        Pythonic iteration; saves users from zipping two parallel lists.
        """
        if len(self.batch_results) != len(self.errors):
            raise ValueError(
                f"length mismatch: batch_results={len(self.batch_results)} "
                f"errors={len(self.errors)}"
            )
        out: list[BatchResult] = []
        for i, (r, e) in enumerate(zip(self.batch_results, self.errors, strict=True)):
            if e is None:
                out.append(BatchSuccess(index=i, response=r))
            else:
                out.append(BatchFailure(index=i, error=e))
        return out


class PdfPage(_Frozen):
    page: int
    page_index: int
    dpi: int
    width: int
    height: int
    results: list[TextItem]
    layout: list[LayoutBox] = Field(default_factory=list)
    reading_order: list[int] = Field(default_factory=list)
    blocks: list[Block] = Field(default_factory=list)
    mode: PdfMode
    text_layer_quality: str

    def _as_ocr_response(self) -> OcrResponse:
        return OcrResponse(
            results=self.results,
            layout=self.layout,
            reading_order=self.reading_order,
            blocks=self.blocks,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def tables(self) -> list[Table]:
        return _synthesize_tables(self.blocks)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def formulas(self) -> list[Formula]:
        return _synthesize_formulas(self.blocks)


class PdfResponse(_Frozen):
    """Multi-page PDF OCR result returned by `recognize_pdf`.

    Attributes:
        pages: One [`PdfPage`][turboocr.PdfPage] per input page, in order.
            Each page carries its own `results`, optional `layout`,
            `reading_order`, `blocks`, plus per-page metadata (`page`,
            `page_index`, `dpi`, `width`, `height`, `mode`,
            `text_layer_quality`).
        text: Cached property — full document text joined across pages
            with blank-line separators.
        tables: Flattened view of `tables` across every page.
        formulas: Flattened view of `formulas` across every page.
    """

    pages: list[PdfPage]

    @cached_property
    def text(self) -> str:
        return "\n\n".join(p._as_ocr_response().text for p in self.pages)

    @property
    def tables(self) -> list[Table]:
        return [t for p in self.pages for t in p.tables]

    @property
    def formulas(self) -> list[Formula]:
        return [f for p in self.pages for f in p.formulas]


class HealthStatus(_Frozen):
    ok: bool
    status_code: int
    body: str
    body_json: dict[str, object] | None = None

"""PyMuPDF + Tesseract engine.

Commentary/judgment pages are OCR'd as prose. Markdown tables are emitted
only when PyMuPDF finds a real grid (not TSV column-guessing on body text).
"""

from __future__ import annotations

import os
import statistics
from pathlib import Path

import fitz

from slip_pdf_md.cleaning import clean_ocr_text, collapse_leaders, normalize_text
from slip_pdf_md.engines.base import ConversionResult

TESSERACT_WINDOWS = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
UNRECOVERED = (
    "> **UNRECOVERED TABLE REGION**\n"
    "> A table-like region was detected on this page but cell text could not "
    "be recovered faithfully. Surrounding extractable text is preserved. "
    "Do not invent missing cells."
)
X_GAP_PX = 25
Y_BUCKET = 8
MIN_TABLE_ROWS = 3
MIN_TABLE_COLS = 2
MAX_MEDIAN_CELL_CHARS = 80
OCR_PSM_PROSE = "4"


def configure_tesseract() -> str | None:
    try:
        import pytesseract
    except ImportError:
        return None
    if TESSERACT_WINDOWS.exists():
        pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_WINDOWS)
        os.environ["PATH"] = str(TESSERACT_WINDOWS.parent) + os.pathsep + os.environ.get("PATH", "")
        return str(TESSERACT_WINDOWS)
    cmd = getattr(pytesseract.pytesseract, "tesseract_cmd", None) or "tesseract"
    return str(cmd)


def _page_image(page: fitz.Page, scale: float = 3.0):
    from PIL import Image

    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    image = image.convert("L")
    # milder than 180: keep thin book type
    image = image.point(lambda x: 255 if x > 165 else 0)
    return image


def ocr_page_text(page: fitz.Page, psm: str = OCR_PSM_PROSE) -> str:
    try:
        import pytesseract
    except ImportError:
        return ""
    configure_tesseract()
    try:
        image = _page_image(page)
        text = pytesseract.image_to_string(
            image,
            config=f"--psm {psm} --oem 3 -c preserve_interword_spaces=1",
        )
        cleaned = clean_ocr_text(text)
        if len(cleaned.split()) < 20 and psm != "3":
            extra = pytesseract.image_to_string(
                image, config="--psm 3 --oem 3 -c preserve_interword_spaces=1"
            )
            extra_c = clean_ocr_text(extra)
            if len(extra_c.split()) > len(cleaned.split()):
                return extra_c
        return cleaned
    except Exception:
        return ""


def _ocr_layout_rows(page: fitz.Page) -> list[list[dict]]:
    try:
        import pytesseract
        from pytesseract import Output
    except ImportError:
        return []
    configure_tesseract()
    try:
        image = _page_image(page)
        data = pytesseract.image_to_data(
            image, config="--psm 6 --oem 3", output_type=Output.DICT
        )
    except Exception:
        return []

    rows: dict[int, list[dict]] = {}
    texts = data.get("text", [])
    lefts = data.get("left", [])
    tops = data.get("top", [])
    widths = data.get("width", [])
    confs = data.get("conf", [])

    for idx, raw_text in enumerate(texts):
        text = (raw_text or "").strip()
        if not text:
            continue
        try:
            conf = int(float(confs[idx])) if idx < len(confs) and confs[idx] != "" else 0
        except Exception:
            conf = 0
        if conf < 0:
            continue
        x = int(lefts[idx]) if idx < len(lefts) else 0
        y = int(tops[idx]) if idx < len(tops) else 0
        width = int(widths[idx]) if idx < len(widths) else 0
        if len(text) <= 1 and not any(ch.isalnum() for ch in text):
            continue
        row_key = (y // Y_BUCKET) * Y_BUCKET
        rows.setdefault(row_key, []).append({"text": text, "x": x, "width": width, "conf": conf})

    grouped = []
    for row_words in sorted(rows.items(), key=lambda item: item[0]):
        ordered = sorted(row_words[1], key=lambda item: item["x"])
        if not ordered:
            continue
        joined = " ".join(item["text"] for item in ordered)
        if len(ordered) >= 2 or len(joined) >= 4:
            grouped.append(ordered)
    return grouped


def _rows_to_markdown_table(rows: list[list[dict]]) -> tuple[str, bool]:
    markdown_rows = []
    saw_aligned = False
    for row_words in rows:
        word_groups: list[list[dict]] = []
        for word in row_words:
            if not word_groups:
                word_groups.append([word])
                continue
            prev = word_groups[-1][-1]
            if word["x"] - (prev["x"] + prev["width"]) > X_GAP_PX:
                word_groups.append([word])
            else:
                word_groups[-1].append(word)
        if len(word_groups) >= 2:
            saw_aligned = True
        cells = []
        for group in word_groups:
            text = " ".join(item["text"] for item in group)
            cleaned = clean_ocr_text(text)
            if cleaned:
                cells.append(cleaned)
        if len(cells) < 2:
            continue
        markdown_rows.append("| " + " | ".join(cells) + " |")

    if len(markdown_rows) >= MIN_TABLE_ROWS:
        header = markdown_rows[0]
        col_count = max(2, header.count("|") - 1)
        separator = "| " + " | ".join(["---"] * col_count) + " |"
        return "\n".join([header, separator, *markdown_rows[1:]]), False
    if saw_aligned and len(markdown_rows) < 2:
        return "", True
    return "", False


def _table_cells(table) -> list[list[str]]:
    extract = getattr(table, "extract", None)
    if not callable(extract):
        return []
    try:
        raw = extract()
    except Exception:
        return []
    rows = []
    for row in raw or []:
        cells = [normalize_text(str(c or "")).strip() for c in row]
        if any(cells):
            rows.append(cells)
    return rows


def is_real_grid(table) -> bool:
    """Reject PyMuPDF false tables on commentary pages."""
    rows = _table_cells(table)
    if len(rows) < MIN_TABLE_ROWS:
        return False
    widths = [len(r) for r in rows]
    if max(widths) < MIN_TABLE_COLS:
        return False
    mode = max(set(widths), key=widths.count)
    if mode < MIN_TABLE_COLS:
        return False
    consistent = sum(1 for w in widths if w == mode) / len(widths)
    if consistent < 0.6:
        return False
    cell_lens = [len(c) for r in rows for c in r if c]
    if not cell_lens:
        return False
    try:
        median = statistics.median(cell_lens)
    except statistics.StatisticsError:
        median = sum(cell_lens) / len(cell_lens)
    if median > MAX_MEDIAN_CELL_CHARS:
        return False
    long_cells = sum(1 for n in cell_lens if n > 160)
    if long_cells / len(cell_lens) > 0.3:
        return False
    return True


def extract_real_tables(page: fitz.Page) -> tuple[str, bool]:
    try:
        table_finder = page.find_tables()
        tables = getattr(table_finder, "tables", []) or []
    except Exception:
        tables = []

    markdown_tables = []
    for table in tables or []:
        if not is_real_grid(table):
            continue
        try:
            table_md = table.to_markdown()
        except Exception:
            continue
        cleaned = normalize_text(table_md)
        if "|" in cleaned and cleaned.count("|") >= 4 and "---" in cleaned:
            markdown_tables.append(collapse_leaders(cleaned))

    if markdown_tables:
        return "\n\n".join(markdown_tables), False
    return "", False


def extract_page(page: fitz.Page) -> tuple[str, bool]:
    native = collapse_leaders(normalize_text(page.get_text("text") or ""))
    ocr = ""
    if len(native.split()) < 25:
        ocr = ocr_page_text(page)
    prose = native if len(native.split()) >= len((ocr or "").split()) else ocr

    table_md, unrecovered = extract_real_tables(page)

    if table_md and prose.strip():
        # Keep reading order: prose first unless the page is mostly the grid
        if len(prose.split()) > 40:
            body = prose.strip() + "\n\n" + table_md
        else:
            body = table_md + "\n\n" + prose.strip()
        if unrecovered:
            body = UNRECOVERED + "\n\n" + body
        return body.strip(), unrecovered

    if table_md:
        body = table_md
        if unrecovered:
            body = UNRECOVERED + "\n\n" + body
        return body.strip(), unrecovered

    if unrecovered and prose.strip():
        return UNRECOVERED + "\n\n" + prose.strip(), True

    if prose.strip():
        return prose.strip(), False
    return "", False


class PyMuPdfTesseractEngine:
    name = "pymupdf+tesseract"

    def convert(self, pdf_path: Path) -> ConversionResult:
        configure_tesseract()
        doc = fitz.open(pdf_path)
        pages: list[str] = []
        warnings: list[str] = []
        unrecovered_tables = 0
        try:
            total_pages = len(doc)
            cb = getattr(self, "on_progress", None)
            for page_number in range(total_pages):
                page = doc[page_number]
                try:
                    body, unrecovered = extract_page(page)
                except Exception as exc:
                    warnings.append(f"page {page_number + 1}: {exc}")
                    body, unrecovered = "", False
                if unrecovered:
                    unrecovered_tables += 1
                pages.append(body)
                if cb:
                    cb((page_number + 1) / max(total_pages, 1), f"OCR page {page_number + 1}/{total_pages}")
        finally:
            doc.close()

        page_count = len(pages)
        nonempty = sum(1 for p in pages if p.strip())
        needs_review = page_count == 0 or nonempty == 0
        if needs_review:
            warnings.append("no extractable text or OCR text was found")
        return ConversionResult(
            pages=pages,
            page_count=page_count,
            engine=self.name,
            warnings=warnings,
            unrecovered_tables=unrecovered_tables,
            needs_review=needs_review,
        )

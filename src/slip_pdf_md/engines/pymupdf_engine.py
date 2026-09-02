"""PyMuPDF + Tesseract engine. Reference: legacy/convert_pdfs.py."""

from __future__ import annotations

import os
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


def _page_image(page: fitz.Page):
    from PIL import Image

    pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), alpha=False)
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    image = image.convert("L")
    image = image.point(lambda x: 255 if x > 180 else 0)
    return image


def ocr_page_text(page: fitz.Page) -> str:
    try:
        import pytesseract
    except ImportError:
        return ""
    configure_tesseract()
    try:
        image = _page_image(page)
        text = pytesseract.image_to_string(
            image, config="--psm 6 --oem 3 -c preserve_interword_spaces=1"
        )
        return clean_ocr_text(text)
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
    """Return (markdown, unrecovered). Unrecovered means aligned columns but empty cells."""
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

    if len(markdown_rows) >= 2:
        header = markdown_rows[0]
        col_count = max(2, header.count("|") - 1)
        separator = "| " + " | ".join(["---"] * col_count) + " |"
        return "\n".join([header, separator, *markdown_rows[1:]]), False
    if saw_aligned and len(markdown_rows) < 2:
        return "", True
    return "", False


def extract_table_markdown(page: fitz.Page) -> tuple[str, bool]:
    try:
        table_finder = page.find_tables()
        tables = getattr(table_finder, "tables", []) or []
    except Exception:
        tables = []

    markdown_tables = []
    for table in tables or []:
        try:
            table_md = table.to_markdown()
        except Exception:
            continue
        cleaned = normalize_text(table_md)
        if "|" in cleaned and cleaned.count("|") >= 4:
            markdown_tables.append(collapse_leaders(cleaned))

    if markdown_tables:
        return "\n\n".join(markdown_tables), False

    rows = _ocr_layout_rows(page)
    if rows:
        legal_table_md, unrecovered = _rows_to_markdown_table(rows)
        if legal_table_md:
            return legal_table_md, False
        if unrecovered:
            return "", True

    return "", False


def extract_page(page: fitz.Page) -> tuple[str, bool]:
    table_md, unrecovered = extract_table_markdown(page)
    text = page.get_text("text")
    cleaned = collapse_leaders(normalize_text(text))

    if table_md:
        if cleaned.strip() and cleaned.strip() not in table_md:
            body = table_md + "\n\n" + cleaned
        else:
            body = table_md
        if unrecovered:
            body = UNRECOVERED + "\n\n" + body
        return body.strip(), unrecovered

    if unrecovered:
        extra = cleaned if cleaned.strip() else ocr_page_text(page)
        parts = [UNRECOVERED]
        if extra.strip():
            parts.append(extra.strip())
        return "\n\n".join(parts), True

    if cleaned.strip():
        return cleaned.strip(), False

    ocr = ocr_page_text(page)
    if ocr.strip():
        return ocr.strip(), False
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
            for page_number in range(len(doc)):
                page = doc[page_number]
                try:
                    body, unrecovered = extract_page(page)
                except Exception as exc:
                    warnings.append(f"page {page_number + 1}: {exc}")
                    body, unrecovered = "", False
                if unrecovered:
                    unrecovered_tables += 1
                pages.append(body)
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

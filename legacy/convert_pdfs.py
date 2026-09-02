import argparse
import os
import re
from pathlib import Path

import fitz
import pytesseract
from PIL import Image
from pytesseract import Output

ROOT = Path(__file__).resolve().parents[1]
RAW_PDF_DIR = ROOT / "0_01_RAW_PDF"
CLEAN_ROOT = ROOT / "20_03_CLEAN_MARKDOWN"

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if Path(TESSERACT_PATH).exists():
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    os.environ["PATH"] = str(Path(TESSERACT_PATH).parent) + os.pathsep + os.environ.get("PATH", "")


def normalize_text(value: str) -> str:
    cleaned = value.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = cleaned.replace("�", "").replace("\x00", "")
    cleaned = cleaned.replace(" .", ".").replace(" ,", ",").replace(" ;", ";")
    lines = []
    for line in cleaned.split("\n"):
        stripped = " ".join(line.strip().split())
        if stripped and not re.fullmatch(r"[-_=]{3,}", stripped):
            lines.append(stripped)
    return "\n".join(lines)


def is_likely_ocr_noise(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True

    lowered = stripped.lower()
    if any(marker in lowered for marker in [
        "lexisnexis",
        "puliani",
        "begun",
        "noc sets",
        "gatiacr",
        "oil",  # common false-positive scan artifact fragment
    ]):
        return True

    if re.fullmatch(r"[-_=#*°@/\\|~`.,;:()'\"\[\]{}]+", stripped):
        return True

    letters = sum(ch.isalpha() for ch in stripped)
    symbols = sum(not (ch.isalnum() or ch.isspace()) for ch in stripped)
    if letters < 4 and symbols > 0:
        return True

    if symbols and len(stripped) > 8:
        symbol_ratio = symbols / len(stripped)
        if symbol_ratio > 0.32 and not any(word in lowered for word in ["the", "and", "for", "law", "criminal", "code", "evidence", "edition", "publisher"]):
            return True

    return False


def clean_ocr_text(value: str) -> str:
    cleaned = normalize_text(value)
    cleaned = re.sub(r"(?<=\w)-\s+(?=\w)", "", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)

    filtered_lines = []
    for line in cleaned.splitlines():
        if not is_likely_ocr_noise(line):
            filtered_lines.append(line.strip())

    cleaned = "\n".join(filtered_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def ocr_page_text(page: fitz.Page) -> str:
    try:
        pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), alpha=False)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        image = image.convert("L")
        image = image.point(lambda x: 255 if x > 180 else 0)
        text = pytesseract.image_to_string(image, config="--psm 6 --oem 3 -c preserve_interword_spaces=1")
        return clean_ocr_text(text)
    except Exception:
        return ""


def _ocr_layout_rows(page: fitz.Page) -> list[list[dict]]:
    try:
        pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), alpha=False)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        image = image.convert("L")
        image = image.point(lambda x: 255 if x > 180 else 0)
        data = pytesseract.image_to_data(
            image,
            config="--psm 6 --oem 3",
            output_type=Output.DICT,
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
        row_key = (y // 8) * 8
        rows.setdefault(row_key, []).append({"text": text, "x": x, "width": width})

    grouped_rows = []
    for row_words in sorted(rows.values(), key=lambda items: min(item["x"] for item in items)):
        ordered = sorted(row_words, key=lambda item: item["x"])
        if not ordered:
            continue
        if len(ordered) >= 2 or len(" ".join(item["text"] for item in ordered)) >= 4:
            grouped_rows.append(ordered)
    return grouped_rows


def _rows_to_markdown_table(rows: list[list[dict]]) -> str:
    markdown_rows = []
    for row_words in rows:
        word_groups: list[list[dict]] = []
        for word in row_words:
            if not word_groups:
                word_groups.append([word])
                continue
            prev = word_groups[-1][-1]
            if word["x"] - (prev["x"] + prev["width"]) > 25:
                word_groups.append([word])
            else:
                word_groups[-1].append(word)

        cells = []
        for group in word_groups:
            text = " ".join(item["text"] for item in group)
            cleaned = clean_ocr_text(text)
            if cleaned:
                cells.append(cleaned)
        if len(cells) < 2:
            continue
        if len(cells) == 2 and re.fullmatch(r"[A-Za-z0-9\s.,;:()/-]+", cells[0]) and len(cells[0]) < 3:
            continue
        markdown_rows.append("| " + " | ".join(cells) + " |")

    if len(markdown_rows) < 3:
        return ""

    header = markdown_rows[0]
    separator = "| " + " | ".join(["---"] * max(2, header.count("|") - 1)) + " |"
    return "\n".join([header, separator, *markdown_rows[1:]])


def extract_table_markdown(page: fitz.Page) -> str:
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
            markdown_tables.append(cleaned)

    if markdown_tables:
        return "\n\n".join(markdown_tables)

    rows = _ocr_layout_rows(page)
    if rows:
        legal_table_md = _rows_to_markdown_table(rows)
        if legal_table_md:
            return legal_table_md

    return ""


def extract_markdown_from_pdf(pdf_path: Path) -> str:
    doc = fitz.open(pdf_path)
    pages = []

    for page_number in range(len(doc)):
        page = doc[page_number]
        table_md = extract_table_markdown(page)

        if table_md:
            pages.append(f"## Page {page_number + 1}\n\n{table_md}")
            continue

        text = page.get_text("text")
        cleaned = normalize_text(text)

        if not cleaned.strip():
            cleaned = ocr_page_text(page)

        if cleaned.strip():
            pages.append(f"## Page {page_number + 1}\n\n{cleaned}")

    doc.close()

    if not pages:
        return "# Empty PDF\n\nNo extractable text or OCR text was found in this document."

    return "\n\n".join(pages)


def find_pdfs(input_dir: Path):
    return sorted(input_dir.rglob("*.pdf"))


def convert_folder(input_dir: Path, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    converted = []

    for pdf_path in find_pdfs(input_dir):
        relative_name = pdf_path.stem
        output_path = output_dir / f"{relative_name}.md"

        try:
            markdown_text = extract_markdown_from_pdf(pdf_path)
            output_path.write_text(markdown_text, encoding="utf-8")
            converted.append(output_path)
        except Exception as exc:
            output_path.write_text(
                f"# Conversion error for {pdf_path.name}\n\n"
                f"This file could not be converted automatically.\n\n"
                f"Error: {exc}\n",
                encoding="utf-8",
            )
            print(f"ERROR {pdf_path.name}: {exc}")
            continue

    return converted


def parse_args():
    parser = argparse.ArgumentParser(description="Convert PDF files to Markdown files.")
    parser.add_argument("--input", type=Path, default=RAW_PDF_DIR, help="Folder containing raw PDF files.")
    parser.add_argument("--output", type=Path, default=CLEAN_ROOT / "markdown", help="Folder for generated Markdown files.")
    return parser.parse_args()


def main():
    args = parse_args()
    input_dir = args.input.resolve()
    output_dir = args.output.resolve()

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    pdf_files = find_pdfs(input_dir)
    if not pdf_files:
        print(f"No PDF files found in {input_dir}.")
        return 0

    converted = convert_folder(input_dir, output_dir)
    print(f"Converted {len(converted)} PDF file(s) to Markdown.")
    for path in converted:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

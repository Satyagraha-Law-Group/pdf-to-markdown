"""Split a READY PDF so no convert job exceeds 100 pages or 100 MB. Happy path."""

from __future__ import annotations

import re
from pathlib import Path

MAX_PAGES_PER_PART = 100
MAX_BYTES_PER_PART = 100 * 1024 * 1024

PAGE_HEADING = re.compile(r"^## Page (\d+)[ \t]*$", re.MULTILINE)
FRONT_MATTER = re.compile(r"^---\n.*?\n---\n*", re.DOTALL)


def pdf_page_count(path: Path) -> int:
    import fitz
    doc = fitz.open(path)
    n = doc.page_count
    doc.close()
    return int(n)


def needs_split(
    path: Path,
    *,
    max_pages: int = MAX_PAGES_PER_PART,
    max_bytes: int = MAX_BYTES_PER_PART,
) -> bool:
    path = Path(path)
    if not path.is_file():
        return False
    if path.stat().st_size > max_bytes:
        return True
    return pdf_page_count(path) > max_pages


def split_pdf(
    source: Path,
    parts_dir: Path,
    *,
    max_pages: int = MAX_PAGES_PER_PART,
    max_bytes: int = MAX_BYTES_PER_PART,
) -> list[Path]:
    """Write part PDFs under parts_dir. Does not modify the source file."""
    import fitz

    source = Path(source)
    parts_dir = Path(parts_dir)
    parts_dir.mkdir(parents=True, exist_ok=True)
    src = fitz.open(source)
    total = src.page_count
    ranges: list[tuple[int, int]] = []
    start = 0
    while start < total:
        end = min(start + max_pages, total)
        while end > start + 1:
            tmp = parts_dir / "_size_probe.pdf"
            probe = fitz.open()
            probe.insert_pdf(src, from_page=start, to_page=end - 1)
            probe.save(tmp)
            probe.close()
            if tmp.stat().st_size <= max_bytes:
                tmp.unlink(missing_ok=True)
                break
            tmp.unlink(missing_ok=True)
            end -= 1
        ranges.append((start, end))
        start = end

    written: list[Path] = []
    nparts = len(ranges)
    stem = source.stem
    for idx, (a, b) in enumerate(ranges, start=1):
        name = f"{stem}-part-{idx:02d}-of-{nparts:02d}.pdf"
        dest = parts_dir / name
        out = fitz.open()
        out.insert_pdf(src, from_page=a, to_page=b - 1)
        out.save(dest)
        out.close()
        written.append(dest)
    src.close()
    return written


def strip_front_matter(text: str) -> str:
    if text.startswith("---"):
        return FRONT_MATTER.sub("", text, count=1)
    return text


def reindex_pages(text: str, offset: int) -> str:
    if offset == 0:
        return text
    def repl(match: re.Match[str]) -> str:
        return f"## Page {int(match.group(1)) + offset}"
    return PAGE_HEADING.sub(repl, text)


def merge_markdown_parts(part_texts: list[str], *, total_pages: int, template: str) -> str:
    """Join part markdown into one document. template already has the right front matter."""
    bodies = []
    offset = 0
    for text in part_texts:
        body = strip_front_matter(text)
        pages_here = len(PAGE_HEADING.findall(body))
        bodies.append(reindex_pages(body, offset).strip())
        offset += pages_here
    merged_body = "\n\n".join(b for b in bodies if b)
    # replace page_count in template front matter
    head = template
    head = re.sub(r"^page_count:.*$", f"page_count: {total_pages}", head, count=1, flags=re.MULTILINE)
    if head.startswith("---"):
        end = head.find("\n---", 3)
        if end >= 0:
            return head[: end + 4] + "\n\n" + merged_body + "\n"
    return template.rstrip() + "\n\n" + merged_body + "\n"


def stem_folder_name(filename: str) -> str:
    return Path(filename).stem

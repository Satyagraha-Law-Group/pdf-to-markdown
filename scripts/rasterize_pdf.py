# -*- coding: utf-8 -*-
"""Rasterize a PDF to Name_raster.pdf at ~220 dpi (PyMuPDF)."""
from __future__ import annotations
import argparse
from pathlib import Path
import pymupdf

def rasterize(src: Path, dpi: int = 220, out: Path | None = None) -> Path:
    src = src.resolve()
    if out is None:
        out = src.with_name(src.stem + "_raster.pdf")
    zoom = dpi / 72.0
    mat = pymupdf.Matrix(zoom, zoom)
    doc = pymupdf.open(src)
    out_doc = pymupdf.open()
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=mat, alpha=False)
        w, h = page.rect.width, page.rect.height
        np = out_doc.new_page(width=w, height=h)
        np.insert_image(np.rect, pixmap=pix)
        print(f"page {i+1}/{len(doc)} {pix.width}x{pix.height}")
    out_doc.save(out, deflate=True, garbage=4)
    out_doc.close()
    doc.close()
    print("wrote", out, "bytes", out.stat().st_size)
    return out

def main():
    ap = argparse.ArgumentParser(description="Rasterize PDF to Name_raster.pdf")
    ap.add_argument("input", type=Path)
    ap.add_argument("--dpi", type=int, default=220)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    rasterize(args.input, dpi=args.dpi, out=args.out)

if __name__ == "__main__":
    main()

"""Session audit-and-control markdown. Precursor to the SHA-256 registry.

Every routing and convert step is appended as a table row so a crash still
leaves a control file. Living database identity remains Document-Hash-Registry.
"""

from __future__ import annotations

from pathlib import Path

from slip_pdf_md.branding import DISCLAIMER, footer_markdown, header_markdown
from slip_pdf_md.naming import iso_calcutta, now_calcutta, three_word_filename
from slip_pdf_md.paths import SlipPaths
from slip_pdf_md.runlog import logs_dir


class SessionAudit:
    def __init__(self, paths: SlipPaths, *, engine: str = "", force: bool = False):
        self.paths = paths
        self.engine = engine
        self.force = force
        self.started = now_calcutta()
        folder = logs_dir(paths)
        self.path = folder / three_word_filename(
            "Audit", "Control", "Session", ext="md", moment=self.started
        )
        self.seq = 0
        self.path.write_text(self._header(), encoding="utf-8")

    def _header(self) -> str:
        return "\n".join(
            [
                header_markdown().rstrip(),
                "",
                "# Audit Control Session",
                "",
                "Precursor to the Document-Hash-Registry. Filename is not identity.",
                "Files are processed sequentially. Each row is one control step.",
                "",
                f"- started_at: `{iso_calcutta(self.started)}`",
                f"- engine: `{self.engine or '(chosen at convert)'}`",
                f"- force: `{self.force}`",
                f"- vault: `{self.paths.root}`",
                "",
                f"> {DISCLAIMER}",
                "",
                "| seq | time | file | sha256 | step | detail |",
                "| ---: | --- | --- | --- | --- | --- |",
                "",
            ]
        )

    def step(self, filename: str, sha256: str, step: str, detail: str = "") -> None:
        self.seq += 1
        sha = (sha256 or "")[:16]
        file_cell = str(filename or "").replace("|", "/")
        detail_cell = str(detail or "").replace("|", "/")
        line = (
            f"| {self.seq} | {iso_calcutta()} | `{file_cell}` | `{sha}` "
            f"| {step} | {detail_cell} |"
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def close(self) -> Path:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write("\n")
            handle.write(f"- finished_at: `{iso_calcutta()}`\n")
            handle.write(f"- steps: {self.seq}\n")
            handle.write(footer_markdown())
        return self.path


def collect_sequential_pdfs(paths: SlipPaths) -> list[Path]:
    """READY leftovers first (crash queue), then RAW drops. Sequential, unique."""
    ordered: list[Path] = []
    seen: set[str] = set()
    for folder in (paths.ready, paths.raw):
        if not folder.is_dir():
            continue
        found = sorted(folder.rglob("*.pdf")) + sorted(folder.rglob("*.PDF"))
        for pdf in found:
            if "parts" in pdf.parts:
                continue
            try:
                key = str(pdf.resolve()).lower()
            except OSError:
                key = str(pdf).lower()
            if key in seen:
                continue
            seen.add(key)
            ordered.append(pdf)
    return ordered

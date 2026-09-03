from datetime import datetime, timedelta, timezone
from pathlib import Path

from slip_pdf_md.paths import SlipPaths
from slip_pdf_md.sessionlog import write_session_summary


def test_session_summary_writes_three_word_name(tmp_path: Path):
    root = tmp_path / "SLIP_DOCUMENT_PROCESSING"
    for name in [
        "0_01_RAW_PDF",
        "10_02_READY_FOR_DOCLING",
        "20_03_CLEAN_MARKDOWN",
        "30_04_CASE_BRIEFS",
        "40_05_PROJECT_BRIEFS",
        "50_90_DUPLICATES",
        "60_90_PROCESSED",
        "70_99_NEEDS_REVIEW",
        "90_00_PROJECT_TOOLING",
        "Convert-PDF-TO-MARKDOWN-01",
    ]:
        (root / name).mkdir(parents=True)
    paths = SlipPaths(root)
    started = datetime(2026, 9, 3, 4, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    finished = started + timedelta(seconds=12)
    dest = write_session_summary(
        paths,
        [
            {
                "status": "DONE",
                "duplicate": False,
                "source_file": "scan.pdf",
                "page_count": 2,
                "output": "out.md",
                "input_bytes": 100,
            }
        ],
        engine="mistral",
        started=started,
        completed=finished,
    )
    assert dest.name.startswith("Session-Convert-Summary-v")
    text = dest.read_text(encoding="utf-8")
    assert "scan.pdf" in text
    assert "mistral" in text
    assert "Satyagraha Law Group" in text
    assert "not legal advice" in text.lower() or "Not legal advice" in text or "not a solicitation" in text

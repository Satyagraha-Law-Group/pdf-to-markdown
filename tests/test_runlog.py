from pathlib import Path

import fitz

from slip_pdf_md.convert import convert_pdf
from slip_pdf_md.registry import Registry


def _text_pdf(path: Path, text: str) -> Path:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()
    return path


def test_convert_writes_start_end_and_token_log(slip_tree):
    pdf = _text_pdf(slip_tree.raw / "notice.pdf", "Satyagraha Law Group hears the petition.")
    reg = Registry(slip_tree.registry_path)
    result = convert_pdf(pdf, slip_tree, reg, move_raw=True)
    reg.close()
    assert result["started_at"]
    assert result["completed_at"]
    assert result["completed_at"] >= result["started_at"]
    assert result["duration_ms"] >= 0
    usage = result["token_usage"]
    assert usage["llm_input_tokens"] == 0
    assert usage["llm_output_tokens"] == 0
    assert usage["llm_total_tokens"] == 0
    assert usage["markdown_tokens_estimate"] > 0
    assert usage["equivalent_internal_vision_input_tokens"] == 1105
    jsonl = slip_tree.registry_dir / "logs" / "runs.jsonl"
    md = slip_tree.registry_dir / "logs" / "Conversion-Run-Log.md"
    assert jsonl.is_file()
    line = jsonl.read_text(encoding="utf-8").strip().splitlines()[-1]
    assert "started_at" in line
    assert "token_usage" in line
    table = md.read_text(encoding="utf-8")
    assert "notice.pdf" in table
    assert "llm_total" in table

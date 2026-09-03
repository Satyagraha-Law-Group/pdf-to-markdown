from slip_pdf_md.engines.pymupdf_engine import (
    MIN_TABLE_ROWS,
    _rows_to_markdown_table,
    is_real_grid,
)
from slip_pdf_md.fidelity import alnum_tokens, token_recall


class _FakeTable:
    def __init__(self, rows):
        self._rows = rows

    def extract(self):
        return self._rows


def test_real_citation_grid_accepted():
    table = _FakeTable(
        [
            ["AIR", "1950", "SC", "1"],
            ["AIR", "1951", "SC", "12"],
            ["AIR", "1952", "SC", "99"],
        ]
    )
    assert is_real_grid(table) is True


def test_commentary_paragraphs_rejected_as_table():
    para = (
        "The arbitrator shall give notice to the parties of the date of hearing "
        "and shall proceed in accordance with the principles of natural justice."
    )
    table = _FakeTable([[para, para], [para, para], [para, para]])
    assert is_real_grid(table) is False


def test_two_rows_not_enough():
    table = _FakeTable([["A", "B"], ["C", "D"]])
    assert is_real_grid(table) is False
    assert MIN_TABLE_ROWS >= 3


def test_tsv_helper_still_builds_pipe_table():
    rows = [
        [{"text": "AIR", "x": 10, "width": 30, "conf": 90}, {"text": "1950", "x": 80, "width": 40, "conf": 90}],
        [{"text": "AIR", "x": 10, "width": 30, "conf": 90}, {"text": "1951", "x": 80, "width": 40, "conf": 90}],
        [{"text": "AIR", "x": 10, "width": 30, "conf": 90}, {"text": "1952", "x": 80, "width": 40, "conf": 90}],
    ]
    md, unrecovered = _rows_to_markdown_table(rows)
    assert "|" in md
    assert "AIR" in md
    assert unrecovered is False


def test_token_recall_counts_overlap():
    assert token_recall("AIR 1950 SC 1", "AIR 1950 SC 1") == 1.0
    assert token_recall("alpha beta gamma", "alpha zeta") == 1 / 3
    assert "air" in alnum_tokens("AIR 1950")

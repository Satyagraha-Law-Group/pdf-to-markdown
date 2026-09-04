"""Gap tests so every category in the SLIP suite has a named case."""
from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from slip_pdf_md import PRODUCT_NAME
from slip_pdf_md.cli import build_parser
from slip_pdf_md.convert import convert_pdf
from slip_pdf_md.doctor import run_doctor
from slip_pdf_md.registry import STATUS_APPROVED, STATUS_AWAITING_APPROVAL, Registry
from slip_pdf_md.test_report import write_product_faqs


def _text_pdf(path: Path, text: str) -> Path:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()
    return path


@pytest.mark.smoke
def test_package_imports():
    """Package imports.

    The product imports and names itself PDF to Markdown.
    """
    assert "PDF" in PRODUCT_NAME


@pytest.mark.integrity
def test_repository_layout_matches_product_surfaces():
    """Repository layout matches the product surfaces.

    src/slip_pdf_md holds the CLI, convert pipeline, engines, registry, and support modules.
    tests proves behavior. web holds the FastAPI app. docs and playbooks hold guides.
    Packaging and key dependencies live in pyproject.toml.
    """
    root = Path(__file__).resolve().parents[1]
    assert (root / "src" / "slip_pdf_md" / "cli.py").is_file()
    assert (root / "src" / "slip_pdf_md" / "convert.py").is_file()
    assert (root / "src" / "slip_pdf_md" / "engines" / "pymupdf_engine.py").is_file()
    assert (root / "src" / "slip_pdf_md" / "registry.py").is_file()
    assert (root / "tests").is_dir()
    assert (root / "web" / "app.py").is_file()
    assert (root / "docs").is_dir()
    assert (root / "playbooks").is_dir()
    assert (root / "scripts").is_dir()
    assert (root / "pyproject.toml").is_file()


@pytest.mark.integrity
def test_product_faq_html_renders_inline_code(tmp_path):
    """FAQ HTML keeps inline code literals.

    Backtick-delimited paths and filenames in FAQ answers become HTML code spans.
    """
    _, html = write_product_faqs(tmp_path)
    text = html.read_text(encoding="utf-8")
    assert "<code>src/slip_pdf_md</code>" in text
    assert "<code>pyproject.toml</code>" in text


@pytest.mark.smoke
def test_cli_help_lists_lawyer_commands():
    """CLI help lists lawyer commands.

    convert, approve, report, and doctor are the lawyer-facing commands.
    """
    parser = build_parser()
    text = parser.format_help()
    for word in ("convert", "approve", "report", "doctor", "catalog"):
        assert word in text


@pytest.mark.smoke
def test_doctor_on_fresh_tree(slip_tree):
    """Doctor on a fresh tree.

    doctor runs on a new SLIP folder set.
    """
    report = run_doctor(slip_tree)
    assert "checks" in report
    names = {c["name"] for c in report["checks"]}
    assert "python" in names


@pytest.mark.security
def test_gitignore_keeps_secrets_out():
    """SECRETS stay gitignored.

    Real keys live in gitignored SECRETS.txt and must not enter git.
    """
    root = Path(__file__).resolve().parents[1]
    gitignore = (root / ".gitignore").read_text(encoding="utf-8")
    assert "SECRETS" in gitignore


@pytest.mark.integrity
def test_convert_yaml_has_required_keys(slip_tree):
    """Staged markdown has required YAML.

    Front matter carries document type, SHA-256, status, engine, and page count.
    """
    pdf = _text_pdf(slip_tree.raw / "notice.pdf", "Satyagraha Law Group hears the petition.")
    reg = Registry(slip_tree.registry_path)
    result = convert_pdf(pdf, slip_tree, reg, move_raw=True)
    reg.close()
    text = Path(result["output"]).read_text(encoding="utf-8")
    for key in ("document_type:", "source_sha256:", "processing_status:", "engine:", "page_count:"):
        assert key in text
    assert "AWAITING_APPROVAL" in text


@pytest.mark.performance
def test_small_convert_finishes_promptly(slip_tree):
    """Small PDF converts promptly.

    A one-page text PDF finishes convert in under thirty seconds.
    """
    import time

    pdf = _text_pdf(slip_tree.raw / "quick.pdf", "Prompt convert for Satyagraha Law Group.")
    reg = Registry(slip_tree.registry_path)
    started = time.perf_counter()
    result = convert_pdf(pdf, slip_tree, reg, move_raw=True)
    elapsed = time.perf_counter() - started
    reg.close()
    assert result["status"] == STATUS_AWAITING_APPROVAL
    assert elapsed < 30


@pytest.mark.uat
def test_lawyer_photocopier_story(slip_tree):
    """Ingestion story.

    Drop PDF, convert, open markdown, see awaiting approval, lawyer approves, GUBERNATIO closes.
    """
    pdf = _text_pdf(slip_tree.raw / "petition.pdf", "Let noble thoughts come to us from every side.")
    reg = Registry(slip_tree.registry_path)
    result = convert_pdf(pdf, slip_tree, reg, move_raw=True)
    sha = result["sha256"]
    assert result["status"] == STATUS_AWAITING_APPROVAL
    md = Path(result["output"])
    assert md.is_file()
    assert "Let noble thoughts" in md.read_text(encoding="utf-8")
    assert reg.gubernatio_loop_closed(sha) is False
    report = reg.write_awaiting_approval_report(slip_tree.registry_dir)
    assert "Awaiting-Approval-Report-v1-" in report.name
    approved = reg.approve(sha, by="Anil B")
    assert approved["status"] == STATUS_APPROVED
    assert reg.gubernatio_loop_closed(sha) is True
    reg.close()

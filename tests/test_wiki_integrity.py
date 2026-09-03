from pathlib import Path

from slip_pdf_md.branding import WIKI_CATALOG, footer_markdown, tool_root
from slip_pdf_md.user_guide import write_lawyer_user_guide
from slip_pdf_md.wiki_graph import check_wiki_graph, extract_wiki_names


def test_site_footer_includes_index_content():
    foot = footer_markdown()
    assert "Founded by Anil B. (Lawyer)" in foot
    assert "https://calendly.com/anil-satyagraha/15min" in foot
    assert "https://www.satyagraha.com" in foot
    assert "Need Legal Help" in foot
    assert "youtube.com/@satyagrahalawgroup2002" in foot


def test_user_guide_wiki_graph_integrity(tmp_path, monkeypatch):
    root = tmp_path / "tool"
    (root / "docs").mkdir(parents=True)
    (root / "playbooks").mkdir()
    (root / "README.md").write_text("# README\n", encoding="utf-8")
    (root / "Lawyer-Instruction-Guide.md").write_text("# Lawyer\n", encoding="utf-8")
    (root / "Tool-Creation-Memory-v1-03-09-2026-05-05-24.md").write_text("# mem\n", encoding="utf-8")
    (root / "Session-Learning-Notes-v1-03-09-2026-05-05-24.md").write_text("# notes\n", encoding="utf-8")
    for name, hint, _ in WIKI_CATALOG:
        if hint in {"README.md", "Lawyer-Instruction-Guide.md",
                    "Tool-Creation-Memory-v1-03-09-2026-05-05-24.md",
                    "Session-Learning-Notes-v1-03-09-2026-05-05-24.md"}:
            continue
        dest = root / hint
        if dest.suffix:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(f"# {name}\n", encoding="utf-8")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            (dest.parent / f"{Path(hint).name}-v1-03-09-2026-00-00-00.md").write_text(f"# {name}\n", encoding="utf-8")
    md, html = write_lawyer_user_guide(root)
    assert md.is_file() and html.is_file()
    names = extract_wiki_names(md.read_text(encoding="utf-8"))
    catalog = {n for n, _, _ in WIKI_CATALOG}
    extra = [n for n in names if n not in catalog]
    assert extra == [], extra
    report = check_wiki_graph(root)
    assert report["ok"], report


def test_live_user_guide_integrity_when_present():
    root = tool_root()
    if not (root / "docs").is_dir():
        return
    from slip_pdf_md.wiki_graph import find_user_guide
    if find_user_guide(root) is None:
        return
    report = check_wiki_graph(root)
    assert report["ok"], report

def test_footer_is_not_duplicated_and_has_no_photocopier():
    from slip_pdf_md.branding import PUBLISH_LINE, footer_markdown, with_single_footer
    foot = footer_markdown()
    assert foot.count(PUBLISH_LINE) == 1
    assert "photocopier" not in foot.lower()
    doubled = foot + "\n" + foot
    cleaned = with_single_footer("Body of the guide.\n" + doubled)
    assert cleaned.count(PUBLISH_LINE) == 1
    assert cleaned.count("Founded by Anil B. (Lawyer)") == 1
    assert "photocopier" not in cleaned.lower()
    assert cleaned.strip().startswith("Body of the guide.")

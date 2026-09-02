from slip_pdf_md.paths import SLIP_DIR_NAMES
from slip_pdf_md.scaffold import create_slip_tree


def test_deploy_creates_folders(tmp_path):
    paths = create_slip_tree(tmp_path / "vault")
    for name in SLIP_DIR_NAMES:
        folder = paths.root / name
        assert folder.is_dir(), name
        assert (folder / ".gitkeep").exists()
    assert paths.raw.name == "0_01_RAW_PDF"
    assert paths.clean.name == "20_03_CLEAN_MARKDOWN"
    assert paths.duplicates.name == "50_90_DUPLICATES"
    assert paths.needs_review.name == "70_99_NEEDS_REVIEW"

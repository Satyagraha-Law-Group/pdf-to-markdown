from slip_pdf_md.citations import repair_citations


def test_citation_repairs_and_attribute_untouched():
    sample = "\n".join(
        [
            "See ATR 1973 SC 1 on ATTRIBUTE mapping.",
            "The Calcutta L] and the AIL) ER cite Caleutta and Jnarkhand s. I71-B.",
        ]
    )
    out = repair_citations(sample)
    assert "AIR 1973 SC 1" in out
    assert "ATTRIBUTE" in out
    assert "ATR" not in out.replace("ATTRIBUTE", "")
    assert "LJ" in out
    assert "All." in out
    assert "Calcutta" in out
    assert "Jharkhand" in out
    assert "171-B" in out
    assert "Caleutta" not in out
    assert "Jnarkhand" not in out
    assert "I71-B" not in out

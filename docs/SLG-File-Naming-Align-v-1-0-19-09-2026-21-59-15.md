# Satyagraha Law Group

**TOOLS · Convert-PDF-TO-MARKDOWN-01 · naming**

# File naming aligned to SLG stamp (19-09-2026-21-59-15)

All generated files now use:

`SLG-<≤3-Title-Case-words>-v-<version>-<subversion>-dd-mm-yyyy-hh-mm-ss.ext`

- Module: `src/slip_pdf_md/naming.py` (`slg_filename`, `three_word_filename`, `convert_output_filename`, `resolve_generated_path`)
- Convert Markdown outputs use `convert_output_filename(pdf_name)` (words from PDF stem)
- Error / fidelity notes use the same pattern with a final word `Error` / `Fidelity`
- Living registry/logs keep first-created stamp; legacy three-word names migrate on open

Converted PDF **folder** stems under READY/PROCESSED are unchanged (routing only).

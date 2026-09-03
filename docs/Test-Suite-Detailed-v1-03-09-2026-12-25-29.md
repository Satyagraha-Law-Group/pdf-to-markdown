# Satyagraha Law Group

**SLIP PDF to Markdown Ingestion Tool**  ·  SLIP  ·  Legal Research  ·  Practitioner-Scholar

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

[https://www.satyagraha.com](https://www.satyagraha.com)

> This is a research project at Satyagraha Law Group as part of its pursuit of excellence in legal research. It is not legal advice, not a solicitation, and not an offer to represent anyone.

---

# Test Suite Detailed

Satyagraha Law Group — SLIP PDF to Markdown Ingestion Tool.
Every test case in TEST_CASES, this run's result, and files processed this day.

- written_at: 2026-09-03T13:38:56+05:30
- run_day: 2026-09-03
- run_id: 2

## Test cases

| Test Case Number | Function | Test Case Name | Description | Category | Result |
| --- | --- | --- | --- | --- | --- |
| TC-FID-001 | `test_error_codes_are_seeded_and_classified` | Error codes are classified | ERROR_CODES is seeded with type, HIGH/MEDIUM/LOW category, message, and resolution. | integrity | PASS |
| TC-FID-002 | `test_register_error_upserts_and_publishes` | New errors publish to the catalog | Registering a code updates ERROR_CODES and the markdown/HTML error table. | integrity | PASS |
| TC-FID-003 | `test_test_case_upsert_keeps_stable_id` | Test case IDs stay stable | Updating a test case keeps TC-XXX-NNN. A new function gets the next number. | integrity | PASS |
| TC-FID-004 | `test_convert_writes_process_run_metrics` | Convert writes process-run metrics | Each convert records day, filename, PDF pages, markdown pages, API key type, and approval status. | integrity | PASS |
| TC-FID-005 | `test_reports_generate_from_catalog_tables` | Reports come from the catalog tables | Detailed and summary test reports are generated from TEST_CASES and TEST_RUNS. | integrity | PASS |
| TC-FID-006 | `test_convert_yaml_has_required_keys` | Staged markdown has required YAML. | Front matter carries document type, SHA-256, status, engine, and page count. | integrity | PASS |
| TC-FID-007 | `test_real_citation_grid_accepted` | Citation grid accepted as table | A genuine citation grid is kept as a table. | integrity | PASS |
| TC-FID-008 | `test_commentary_paragraphs_rejected_as_table` | Commentary is not a table | Prose commentary is not forced into a pipe table. | integrity | PASS |
| TC-FID-009 | `test_two_rows_not_enough` | Two rows are not a table | A two-row fragment is not promoted to a table. | integrity | PASS |
| TC-FID-010 | `test_token_recall_counts_overlap` | Token recall measures overlap | Fidelity recall counts overlapping tokens between PDF and markdown. | integrity | PASS |
| TC-FID-011 | `test_convert_writes_token_usage_column` | Token usage column on convert | Each PDF-to-markdown run stores token_usage on documents, GUBERNATIO, YAML, and the run log. | integrity | PASS |
| TC-FID-012 | `test_registry_alters_token_usage_on_existing_db` | Live registry gains token_usage | Opening an older sqlite adds the token_usage column to documents and GUBERNATIO. | integrity | PASS |
| TC-FID-013 | `test_verify_synthetic_markdown` | Verify checks a markdown file | verify reports PASS/FAIL on required front matter and structure. | integrity | PASS |
| TC-FID-014 | `test_user_guide_wiki_graph_integrity` | User guide wiki graph | The lawyer user guide wiki-links every related file. Obsidian can graph them. HTML hrefs resolve. | integrity | PASS |
| TC-FID-015 | `test_live_user_guide_integrity_when_present` | Live user guide integrity check | When the tool folder has the user guide, every wiki link and HTML href resolves. | integrity | PASS |
| TC-FUN-001 | `test_table_fixture_pdf` | True table becomes markdown table | A real table in a PDF is rendered as a markdown table, not invented cells. | functionality | PASS |
| TC-FUN-002 | `test_text_layer_fixture_pdf` | Text PDF becomes staged markdown | A one-page text PDF converts to markdown with YAML front matter and Page 1, status awaiting approval. | functionality | PASS |
| TC-FUN-003 | `test_needs_review_may_retry` | NEEDS_REVIEW may retry | A file the engine will not stand behind can be converted again. | functionality | PASS |
| TC-FUN-004 | `test_duplicate_notice_names_first_file` | Duplicate notice names the first file | A [DUP] notice points at the original filename and canonical markdown. | functionality | PASS |
| TC-FUN-005 | `test_five_page_file_splits_into_three_parts` | Oversized PDF splits at READY | A file over the page cap is split into parts of at most 100 pages. | functionality | PASS |
| TC-FUN-006 | `test_reindex_and_merge_markdown_parts` | Part markdown merges as one file | Page headings continue 1..N after parts are merged. | functionality | PASS |
| TC-INT-001 | `test_gubernatio_table_exists_and_records_filename` | GUBERNATIO records this filename | Every sighting appends a GUBERNATIO row with filename, host, and agent. documents stays one row per hash. | integration | PASS |
| TC-INT-002 | `test_gubernatio_keeps_documents_lean_on_duplicate_filename` | Rename does not clog identity | The same bytes under a new name stay one documents row. GUBERNATIO keeps both filenames. | integration | PASS |
| TC-INT-003 | `test_convert_writes_gubernatio_on_done_and_duplicate` | Convert writes GUBERNATIO | Convert and a later duplicate both append GUBERNATIO rows. | integration | PASS |
| TC-INT-004 | `test_gubernatio_done_gates_before_registry` | GUBERNATIO is the DONE gate | If GUBERNATIO already extracted a hash, convert parks a duplicate even if documents is empty. | integration | PASS |
| TC-PER-001 | `test_small_convert_finishes_promptly` | Small PDF converts promptly. | A one-page text PDF finishes convert in under thirty seconds. | performance | PASS |
| TC-REG-001 | `test_retries_do_not_double_convert_done_hash` | Same bytes convert once | Dropping the same PDF under a new name parks a duplicate. Markdown is not written twice. | regression | PASS |
| TC-REG-002 | `test_duplicate_goes_to_dated_duplicates_not_processed` | Duplicates go to DUPLICATES | A known hash is moved to dated DUPLICATES, not PROCESSED, and is not converted again. | regression | PASS |
| TC-SEC-001 | `test_require_fingerprint_refuses_raw_key` | Raw API key is refused | A raw secret must not be stored. Only a SHA-256 fingerprint is accepted. | security | PASS |
| TC-SEC-002 | `test_gubernatio_record_refuses_raw_api_key` | GUBERNATIO refuses a raw key | Writing a raw API key into GUBERNATIO is rejected. The fingerprint is stored instead. | security | PASS |
| TC-SEC-003 | `test_different_fingerprints_may_run_in_parallel` | Different keys may run together | Two different API fingerprints may convert at the same time. The same fingerprint may not. | security | PASS |
| TC-SEC-004 | `test_sentinel_name_is_anils_exact_string` | Sentinel name is exact | The lease sentinel is exactly SLG-pdf_to_md_file_naming_convention.text. | security | PASS |
| TC-SEC-005 | `test_second_agent_is_halted_until_release` | Same key cannot dual-run | A second agent using the same key is HALTed until the first releases. | security | PASS |
| TC-SEC-006 | `test_expired_lease_is_not_stuck_forever` | Expired lease is free | After the 15-minute lease expires, the next lawyer is not stuck. | security | PASS |
| TC-SEC-007 | `test_convert_halts_when_mistral_lease_held` | HALT leaves RAW | When the Mistral key is held, convert returns HALTED and does not move the PDF. | security | PASS |
| TC-SEC-008 | `test_local_engine_does_not_create_sentinel` | Tesseract creates no sentinel | A local convert does not touch the key-lease sentinel. | security | PASS |
| TC-SEC-009 | `test_missing_api_key` | Missing Mistral key fails closed | Convert with Mistral without a key does not pretend to succeed. | security | PASS |
| TC-SEC-010 | `test_resolve_api_key_from_env` | Key is read from the environment | The Mistral key is taken from the environment or gitignored SECRETS, never from sqlite. | security | PASS |
| TC-SEC-011 | `test_write_templates_do_not_overwrite_real` | Templates do not overwrite real secrets | Writing SECRETS.example never overwrites a real SECRETS.txt. | security | PASS |
| TC-SEC-012 | `test_gitignore_keeps_secrets_out` | SECRETS stay gitignored. | Real keys live in gitignored SECRETS.txt and must not enter git. | security | PASS |
| TC-SMO-001 | `test_deploy_creates_folders` | Init creates the SLIP folders | scaffold creates the ten pipeline folders a lawyer expects. | smoke | PASS |
| TC-SMO-002 | `test_package_imports` | Package imports. | The product imports and names itself PDF to Markdown. | smoke | PASS |
| TC-SMO-003 | `test_cli_help_lists_lawyer_commands` | CLI help lists lawyer commands. | convert, approve, report, and doctor are the lawyer-facing commands. | smoke | PASS |
| TC-SMO-004 | `test_doctor_on_fresh_tree` | Doctor on a fresh tree. | doctor runs on a new SLIP folder set. | smoke | PASS |
| TC-SMO-005 | `test_health_ok` | Web health endpoint | The optional web app answers a health check. | smoke | PASS |
| TC-SYS-001 | `test_audit_writes_three_word_named_report` | Audit report uses three-word name | Quality audit writes a Title-Case three-word filename with a Calcutta stamp. | system | PASS |
| TC-SYS-002 | `test_backfill_gubernatio_from_legacy_sightings` | Legacy sightings backfill GUBERNATIO | An older registry without GUBERNATIO is filled from sightings once. | system | PASS |
| TC-SYS-003 | `test_resolve_migrates_legacy_registry` | Legacy registry name migrates | An old registry.sqlite is resolved to the living three-word sqlite. | system | PASS |
| TC-SYS-004 | `test_backup_created_and_restores_after_delete` | Registry backup restores | If the live sqlite is deleted, the sibling .bak is restored. | system | PASS |
| TC-SYS-005 | `test_rebuild_from_markdown_front_matter` | Rebuild from markdown | If both sqlite copies are gone, the registry rebuilds from YAML front matter. | system | PASS |
| TC-SYS-006 | `test_new_file_moves_raw_to_ready_then_processed` | RAW to READY to PROCESSED | A new PDF moves RAW to READY, then the original parks under PROCESSED. | system | PASS |
| TC-SYS-007 | `test_collect_ready_leftovers_before_raw` | READY leftovers go first | Sequential convert finishes leftover READY files before new RAW files. | system | PASS |
| TC-SYS-008 | `test_collect_skips_split_parts` | Split parts are not collected as originals | Part PDFs under Stem/parts are not treated as new source files. | system | PASS |
| TC-SYS-009 | `test_happy_path_split_convert_merges_and_deletes_parts` | Happy-path split deletes parts | After a clean merge the part PDFs are deleted and the original is processed. | system | PASS |
| TC-UAT-001 | `test_convert_awaits_lawyer_before_gubernatio_closes` | Lawyer must approve before GUBERNATIO closes | A successful convert stages markdown as awaiting approval. Only a lawyer approve closes the loop. | uat | PASS |
| TC-UAT-002 | `test_noninteractive_defaults_local` | Scripts default to local Tesseract | A non-interactive script without --engine stays on the local engine. | uat | PASS |
| TC-UAT-003 | `test_choice_help_names_both_engines` | Help names both engines | The convert prompt names Local Tesseract and Mistral AI. | uat | PASS |
| TC-UAT-004 | `test_force_banner_still_asks` | Force still asks the engine | --force still asks 1 Local Tesseract or 2 Mistral AI. | uat | PASS |
| TC-UAT-005 | `test_interactive_always_prompts_even_if_engine_passed` | Terminal always asks | In a terminal the tool asks even if --engine was passed. | uat | PASS |
| TC-UAT-006 | `test_interactive_choice_two_is_mistral` | Choice 2 is Mistral | Answering 2 selects the Mistral AI engine. | uat | PASS |
| TC-UAT-007 | `test_lawyer_photocopier_story` | Ingestion story. | Drop PDF, convert, open markdown, see awaiting approval, lawyer approves, GUBERNATIO closes. | uat | PASS |
| TC-UAT-008 | `test_site_footer_includes_index_content` | Docs footer matches satyagraha-website | Reports and guides carry the Satyagraha site index footer, including Calendly and the public channels. | uat | PASS |
| TC-UNT-001 | `test_uses_remote_api_placeholder_engines` | Remote API placeholders | Mistral, Docling, Google, Claude, Hermes, and Reducto are remote. Local Tesseract is not. | unit | PASS |
| TC-UNT-002 | `test_citation_repairs_and_attribute_untouched` | Citation repairs leave ATTRIBUTE | Conservative OCR repairs map ATR to AIR and never touch the word ATTRIBUTE. | unit | PASS |
| TC-UNT-003 | `test_tsv_buckets_build_pipe_table` | TSV buckets become a pipe table | Recovered table tokens are joined into a markdown pipe table. | unit | PASS |
| TC-UNT-004 | `test_explicit_aliases` | Engine aliases | pymupdf and mistral aliases resolve to the two engines the lawyer is asked about. | unit | PASS |
| TC-UNT-005 | `test_uses_mistral_only_for_mistral_engines` | Local engine takes no lease | Only Mistral-family names take the Mistral lease. pymupdf does not. | unit | PASS |
| TC-UNT-006 | `test_engine_aliases` | Mistral engine aliases | mistral / mistralai names resolve to the upload engine. | unit | PASS |
| TC-UNT-007 | `test_parse_ocr_pages_keeps_order` | OCR pages keep order | Mistral page payloads stay in document order. | unit | PASS |
| TC-UNT-008 | `test_convert_with_fake_transport` | Mistral fake transport | A stubbed Mistral transport still yields ordered pages. | unit | PASS |
| TC-UNT-009 | `test_three_word_filename_matches_convention` | Three-word filename convention | Generated artifacts match Word1-Word2-Word3-vN-DD-MM-YYYY-HH-MI-SS. | unit | PASS |
| TC-UNT-010 | `test_registry_uniqueness_same_bytes_two_names` | Hash is identity | Two filenames with the same bytes share one SHA-256 row. | unit | PASS |
| TC-UNT-011 | `test_convert_writes_start_end_and_token_log` | Run log has start and end | Each convert writes started, completed, and token estimates. | unit | PASS |
| TC-UNT-012 | `test_parse_setx_line` | SECRETS setx lines parse | Windows setx lines in SECRETS.txt are read. | unit | PASS |
| TC-UNT-013 | `test_parse_key_equals_value` | SECRETS key=value parses | KEY=value lines in SECRETS.txt are read. | unit | PASS |
| TC-UNT-014 | `test_parse_export_and_set` | SECRETS export/set parse | export and set forms in SECRETS.txt are read. | unit | PASS |
| TC-UNT-015 | `test_session_summary_writes_three_word_name` | Session summary three-word name | The convert session summary uses the three-word stamp. | unit | PASS |
| TC-UNT-016 | `test_stem_folder_name_strips_extension` | Stem folder strips extension | READY / PROCESSED stem folders are the filename without .pdf. | unit | PASS |
| TC-UNT-017 | `test_needs_split_page_and_size_caps` | Split caps are 100 pages or 100 MB | needs_split is true only when pages or bytes exceed the cap. | unit | PASS |
| TC-UNT-018 | `test_tsv_helper_still_builds_pipe_table` | TSV helper builds pipes | The TSV helper still emits a markdown pipe table. | unit | PASS |

## Files processed (this day)

Authentic convert metrics: day, filename, PDF pages, markdown pages, API key type, approval status.

| Day | File | PDF pages | Markdown pages | API key type | Status | Approved | SHA-256 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-03 | `Scan2026-08-20_072709.pdf` | 56 | 56 | mistral | DONE | yes | `6c777a9c2976` |

---

Satyagraha Law Group publishes a SLIP PDF to Markdown Ingestion Tool. It does not publish a library.

**Satyagraha Law Group**  ·  SLIP PDF to Markdown Ingestion Tool  ·  SLIP

Founded by Anil B. (Lawyer), Satyagraha Law Group provides legal services for seekers looking for help by searching for Corporate Law, Civil Law, Criminal Law, Writs, High Court Lawyer, NRI Lawyer, Lawyer In Hyderabad, India.

Need Legal Help. [Click here](https://calendly.com/anil-satyagraha/15min).

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

> This is a research project at Satyagraha Law Group as part of its pursuit of excellence in legal research. It is not legal advice, not a solicitation, and not an offer to represent anyone.

[https://www.satyagraha.com](https://www.satyagraha.com)

This site is built from **real-world experience helping clients seeking Justice**, case by case — based on our work involving Legal Research, Drafting, Pleadings, Representation and beyond.

Explore further: [Website](https://www.satyagraha.com) · [YouTube](https://www.youtube.com/@satyagrahalawgroup2002) · [Udemy Courses](https://www.udemy.com/user/anil-b-23/) · [LinkedIn](https://www.linkedin.com/in/anilsatyagraha/) · [Facebook](https://www.facebook.com/satyagrahalawgroup) · [Twitter / X](https://twitter.com/_satyagraha) · [WordPress](https://satyagrahalawgroup.wordpress.com/) · [Instagram](https://www.instagram.com/satyagrahalawgroup/) · [Pinterest](https://in.pinterest.com/satyagrahalawgroup/) · [Tumblr](https://www.tumblr.com/blog/satyagrahalawgroup) · [SoundCloud](https://soundcloud.com/satyagrahalawgroup) · [Podomatic](http://anil-satyagraha.podomatic.com/) · [Newsletter](https://satyagraha.substack.com/) · [WhatsApp](https://api.whatsapp.com/send?phone=917095776633)

Need Legal Help? [Click Here For Next Steps](https://calendly.com/anil-satyagraha/15min)

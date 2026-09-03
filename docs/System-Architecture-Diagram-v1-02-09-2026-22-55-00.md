# Satyagraha Law Group

**PDF to Markdown**  ·  SLIP  ·  Legal Research  ·  Practitioner-Scholar

आ नो भद्राः क्रतवो यन्तु विश्वतः

*Let noble thoughts come to us from every side. — Rig Veda*

*The law is reason, free from passion.*

[https://www.satyagraha.com](https://www.satyagraha.com)

> This is a research project at Satyagraha Law Group as part of its pursuit of excellence in legal research. It is not legal advice, not a solicitation, and not an offer to represent anyone.

---
<!-- Related documents: Obsidian wiki links AND GitHub relative links -->
<!-- [[README]] [[Mistral-Engine-Guide]] [[Marker-Mistral-Engine]] [[Product-Requirements-Spec]] [[System-Design-Document]] [[Implementation-Plan-Guide]] [[System-Architecture-Diagram]] [[Process-Workflow-Guide]] -->

## Related documents

- [[README]] — [Product overview](../README.md)
- [[Mistral-Engine-Guide]] — [Lawyer user guide](Mistral-Engine-Guide-v1-03-09-2026-04-39-31.md)
- [[Marker-Mistral-Engine]] — [Mistral engine mapping](Marker-Mistral-Engine-v1-03-09-2026-04-05-21.md)
- [[Product-Requirements-Spec]] — [Requirements](Product-Requirements-Spec-v1-02-09-2026-22-55-00.md)
- [[System-Design-Document]] — [Design](System-Design-Document-v1-02-09-2026-22-55-00.md)
- [[Implementation-Plan-Guide]] — [Plan](Implementation-Plan-Guide-v1-02-09-2026-22-55-00.md)
- [[System-Architecture-Diagram]] — [Architecture](System-Architecture-Diagram-v1-02-09-2026-22-55-00.md)
- [[Process-Workflow-Guide]] — [Workflow](Process-Workflow-Guide-v1-02-09-2026-22-55-00.md)
# System Architecture Diagram

**Satyagraha Law Group**  
**Product:** SLIP PDF to Markdown Ingestion Tool  
**Family:** SLIP — Satyagraha Law Group Legal Intelligence Platform  
**Document:** System-Architecture-Diagram-v1-02-09-2026-22-55-00  
**Notation:** Mermaid flowcharts plus a black-on-white PNG of the happy path. These diagrams are the contract for implementers.

---

## 0. Convert happy path (split at READY)

White background, black type, black borders.

![Convert happy-path flowchart](Convert-Pipeline-Flowchart-v1-03-09-2026-06-48-52.png)

```mermaid
%%{init: {"theme":"base","themeVariables":{"primaryColor":"#ffffff","primaryTextColor":"#000000","primaryBorderColor":"#000000","lineColor":"#000000","secondaryColor":"#ffffff","tertiaryColor":"#ffffff","background":"#ffffff","mainBkg":"#ffffff","nodeBorder":"#000000","clusterBkg":"#ffffff","titleColor":"#000000","edgeLabelBackground":"#ffffff"}}}%%
flowchart TD
  raw["RAW: whole source PDF"] --> hash["Hash SHA-256"]
  hash --> gub["GUBERNATIO row for this filename"]
  gub --> dup{"Already in registry as DONE?"}
  dup -->|yes| dups["MOVE whole file to 50_90_DUPLICATES / date. Unchanged. No split."]
  dup -->|no| ready["MOVE whole file to 10_02_READY_FOR_DOCLING / date / Stem / Stem.pdf"]
  ready --> inspect{"Pages over 100 or size over 100 MB?"}
  inspect -->|no| one["Convert this one PDF"]
  inspect -->|yes| split["Write parts of at most 100 pages and 100 MB into READY / date / Stem / parts /"]
  split --> conv["Convert each part in order. Never convert the original."]
  conv --> merge["Merge part markdown into ONE file in 20_03_CLEAN_MARKDOWN. Page headings continue 1..N"]
  one --> md["ONE markdown in CLEAN_MARKDOWN"]
  merge --> del["DELETE the part PDFs"]
  del --> proc["MOVE original Stem.pdf to 60_90_PROCESSED / date / Stem / Stem.pdf"]
  md --> proc
  proc --> gubdone["Update documents and GUBERNATIO"]
```

## 1. SLIP folder flow

The lawyer only sees the left-most drop and the right-most Markdown. Everything in the middle is the tool's internals.

```mermaid
flowchart LR
    subgraph lawyer [Lawyer]
        DROP["Drop PDF"]
        OPEN["Open Markdown"]
    end

    subgraph slip [SLIP Document Processing]
        RAW["0_01_RAW_PDF"]
        READY["10_02_READY_FOR_DOCLING"]
        CLEAN["20_03_CLEAN_MARKDOWN"]
        DUP["50_90_DUPLICATES"]
        PROC["60_90_PROCESSED"]
        REV["70_99_NEEDS_REVIEW"]
        BRIEF["30_04_CASE_BRIEFS<br/>40_05_PROJECT_BRIEFS<br/>empty — Layer 2"]
        TOOL["90_00_PROJECT_TOOLING<br/>registry.sqlite"]
        APP["Convert-PDF-TO-MARKDOWN-01"]
    end

    DROP --> RAW
    RAW -->|"new SHA-256"| READY
    RAW -->|"known SHA-256"| DUP
    READY --> APP
    APP -->|"DONE"| CLEAN
    APP -->|"NEEDS_REVIEW"| REV
    RAW -->|"after route"| PROC
    CLEAN --> OPEN
    APP --> TOOL
    BRIEF -.->|"not written by this tool"| CLEAN
```

---

## 2. Phase 1 — local CLI and LLM playbooks

```mermaid
flowchart TB
    subgraph invoke [Invocation]
        HUMAN["Lawyer / clerk in a terminal"]
        AGENT["Any LLM running playbooks/01 to 05"]
        PLAY["playbooks/01-Deploy-Scaffold.md<br/>02-Convert 03-Audit<br/>04-Duplicates 05-Repair"]
    end

    subgraph cli [Level A — slip_pdf_md CLI]
        DOCTOR["doctor"]
        INIT["init"]
        CONVERT["convert"]
        AUDIT["audit"]
    end

    subgraph engine [Level B — Engine adapter]
        PYM["PyMuPDF text layer"]
        TAB["find_tables"]
        OCR["Tesseract OCR"]
        TSV["Tesseract TSV buckets"]
        UNR["UNRECOVERED callout"]
    end

    HUMAN --> DOCTOR
    HUMAN --> INIT
    HUMAN --> CONVERT
    HUMAN --> AUDIT
    AGENT --> PLAY
    PLAY -->|"{{REPO_URL}} {{VAULT}}"| INIT
    PLAY --> CONVERT
    PLAY --> AUDIT
    CONVERT --> PYM
    PYM -->|"tables?"| TAB
    PYM -->|"empty page"| OCR
    TAB -->|"no grid"| TSV
    TSV -->|"aligned but empty"| UNR
```

Playbook invocation is parameterized: the agent is told the GitHub URL `https://github.com/Satyagraha-Law-Group/pdf-to-markdown` and the vault path. It does not scrape credentials. It does not push client files.

---

## 3. SHA-256 registry

Filename is a label. Bytes are identity.

```mermaid
flowchart TB
    FILE["Inbound PDF bytes"]
    HASH["SHA-256"]
    FILE --> HASH
    HASH --> Q{"documents.sha256<br/>already present?"}
    Q -->|no| INS["INSERT documents status=NEW<br/>sighting routed_to=10_02"]
    Q -->|yes DONE| DUP["INSERT sighting routed_to=50_90<br/>copy file + sidecar<br/>DO NOT convert"]
    Q -->|yes PROCESSING| RESUME["Resume single convert<br/>no second document row"]
    Q -->|yes NEEDS_REVIEW| RETRY["Retry allowed<br/>still one document row"]
    INS --> PROC["status=PROCESSING"]
    PROC --> ENG["Engine adapter"]
    RETRY --> ENG
    RESUME --> ENG
    ENG --> OK{"Faithful extract?"}
    OK -->|yes| DONE["status=DONE<br/>write 20_03_CLEAN_MARKDOWN"]
    OK -->|no| NR["status=NEEDS_REVIEW<br/>write 70_99_NEEDS_REVIEW"]
```

Registry location: `90_00_PROJECT_TOOLING/pdf-to-markdown/registry.sqlite`. Unique primary key on `sha256`. Retries must not double-convert `DONE` hashes.

---

## 4. Phase 2 — web (same engine)

```mermaid
flowchart LR
    BROWSER["Browser drop zone<br/>Drop PDF → Wait → Open Markdown"]
    API["FastAPI web.app"]
    POST["POST /jobs"]
    GET["GET /jobs/id"]
    HL["GET /health"]
    BG["Background task"]
    ENG["slip_pdf_md.convert<br/>same engine as CLI"]
    MD["Download .md"]

    BROWSER --> POST
    BROWSER --> GET
    BROWSER --> HL
    POST --> API
    GET --> API
    HL --> API
    POST --> BG
    BG --> ENG
    GET --> MD
```

Default bind `127.0.0.1:8000`. One-liner:

`uvicorn web.app:app --reload --host 127.0.0.1 --port 8000`

---

## 5. Phase 2b — managed Drive / Make.com / Docling (design only)

This diagram is a **future** topology. No code in this sprint implements the dashed nodes.

```mermaid
flowchart LR
    DRIVE["Google Drive inbound"]
    MAKE["Make.com / n8n"]
    WATCH["Watcher — not built"]
    RAW["0_01_RAW_PDF"]
    CLI["slip-pdf-md convert --engine ..."]
    ADAPT["Adapter registry"]
    PYM["pymupdf+tesseract — built"]
    DOC["IBM Docling — not built"]
    MIS["Mistral / Reducto / Document AI — not built"]
    OUT["20_03_CLEAN_MARKDOWN"]

    DRIVE -.-> WATCH
    MAKE -.->|"POST /jobs"| CLI
    WATCH -.-> RAW
    RAW --> CLI
    CLI --> ADAPT
    ADAPT --> PYM
    ADAPT -.-> DOC
    ADAPT -.-> MIS
    PYM --> OUT
```

---

## 6. Component view (packages on disk)

```mermaid
flowchart TB
    subgraph repo [GitHub: Satyagraha-Law-Group/pdf-to-markdown]
        DOCS["docs/ five specifications"]
        PB["playbooks/ 01-05"]
        SRC["src/slip_pdf_md"]
        WEB["web/ FastAPI + static"]
        SCR["scripts/deploy.py"]
        TST["tests/ generated fixtures"]
        SCF["scaffold/SLIP_DOCUMENT_PROCESSING"]
    end

    SRC --> REG["registry.py"]
    SRC --> CV["convert.py"]
    SRC --> ENG["engines/pymupdf_engine.py"]
    SRC --> CL["cli.py"]
    WEB --> CV
    SCR --> SCF
    PB --> CL
```

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

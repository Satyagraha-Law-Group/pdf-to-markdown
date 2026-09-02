# System Architecture Diagram

**Satyagraha Law Group**  
**Product:** PDF to Markdown  
**Family:** SLIP — Satyagraha Law Group Legal Intelligence Platform  
**Document:** System-Architecture-Diagram-v1-02-09-2026-22-55-00  
**Notation:** Mermaid flowcharts. These diagrams are the contract for implementers.

---

## 1. SLIP folder flow

The lawyer only sees the left-most drop and the right-most Markdown. Everything in the middle is the photocopier's internals.

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

## 7. Trust boundary

```mermaid
flowchart TB
    subgraph public [Public GitHub]
        TOOL["Tool source, docs, playbooks, tests"]
    end

    subgraph vault [Private vault disk]
        PDFS["Client PDFs"]
        MD["Clean Markdown"]
        VENV[".venv"]
        DB["registry.sqlite"]
    end

    TOOL -->|"clone / deploy"| VENV
    PDFS -->|"never git add"| TOOL
    MD -->|"gitignored"| TOOL
    DB -->|"gitignored"| TOOL
```

Satyagraha Law Group publishes a photocopier. It does not publish a library.

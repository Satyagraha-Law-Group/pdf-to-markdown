"""Phase 2 web app — same engine as the CLI. Bind localhost."""

from __future__ import annotations

import os
import sys
import threading
import uuid
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from slip_pdf_md import FAMILY, ORG, PRODUCT_NAME  # noqa: E402
from slip_pdf_md.convert import convert_pdf  # noqa: E402
from slip_pdf_md.paths import SlipPaths  # noqa: E402
from slip_pdf_md.registry import Registry  # noqa: E402
from slip_pdf_md.scaffold import create_slip_tree  # noqa: E402

STATIC = Path(__file__).resolve().parent / "static"
JOBS_ROOT = Path(os.environ.get("SLIP_WEB_JOBS", ROOT / "web_jobs"))

app = FastAPI(title=f"{ORG} — {PRODUCT_NAME}", version="1.0.0")
if STATIC.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

_jobs: dict[str, dict] = {}
_lock = threading.Lock()


def _vault() -> SlipPaths:
    env = os.environ.get("SLIP_VAULT")
    if env:
        return create_slip_tree(Path(env))
    mini = JOBS_ROOT / "_vault"
    return create_slip_tree(mini)


def _run_job(job_id: str, pdf_path: Path) -> None:
    with _lock:
        _jobs[job_id]["status"] = "PROCESSING"
    try:
        paths = _vault()
        registry = Registry(paths.registry_path)
        try:
            # Work from a copy in RAW so routing matches the CLI.
            paths.raw.mkdir(parents=True, exist_ok=True)
            inbound = paths.raw / pdf_path.name
            if inbound.resolve() != pdf_path.resolve():
                inbound.write_bytes(pdf_path.read_bytes())
            result = convert_pdf(inbound, paths, registry, move_raw=True)
        finally:
            registry.close()
        with _lock:
            _jobs[job_id].update(
                {
                    "status": result["status"],
                    "duplicate": bool(result.get("duplicate")),
                    "output": result.get("output"),
                    "sha256": result.get("sha256"),
                    "error": result.get("error"),
                }
            )
    except Exception as exc:
        with _lock:
            _jobs[job_id]["status"] = "NEEDS_REVIEW"
            _jobs[job_id]["error"] = str(exc)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "product": PRODUCT_NAME,
        "family": FAMILY,
        "org": ORG,
    }


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    index_path = STATIC / "index.html"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return f"<h1>{ORG}</h1><p>Drop PDF → Wait → Open Markdown</p>"


@app.post("/jobs")
async def create_job(file: UploadFile, background_tasks: BackgroundTasks) -> dict:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Upload a PDF file")
    job_id = str(uuid.uuid4())
    job_dir = JOBS_ROOT / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename).name
    pdf_path = job_dir / safe_name
    payload = await file.read()
    pdf_path.write_bytes(payload)
    with _lock:
        _jobs[job_id] = {
            "id": job_id,
            "status": "NEW",
            "filename": safe_name,
            "output": None,
            "error": None,
        }
    background_tasks.add_task(_run_job, job_id, pdf_path)
    return {"id": job_id, "status": "NEW"}


@app.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    with _lock:
        job = _jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="unknown job")
        body = dict(job)
    if body.get("output"):
        body["download"] = f"/jobs/{job_id}/markdown"
    return body


@app.get("/jobs/{job_id}/markdown")
def download_markdown(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="unknown job")
        output = job.get("output")
    if not output or not Path(output).exists():
        raise HTTPException(status_code=409, detail="markdown not ready")
    return FileResponse(
        output,
        media_type="text/markdown",
        filename=Path(output).name,
    )

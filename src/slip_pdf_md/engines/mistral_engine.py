"""MistralAI OCR engine (same path as Obsidian OCR-AI / marker-api).

Uploads the PDF to Mistral, OCRs with mistral-ocr-latest, maps each page
into SLIP markdown. Requires MISTRAL_API_KEY. Default convert stays local.
"""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from slip_pdf_md.engines.base import ConversionResult
from slip_pdf_md.secrets import DUMMY_KEY, load_secrets

API_ROOT = "https://api.mistral.ai"
OCR_MODEL = "mistral-ocr-latest"
DEFAULT_TIMEOUT_S = 900


class MistralConfigError(RuntimeError):
    """Missing or invalid Mistral settings."""


def resolve_api_key(explicit: str | None = None) -> str:
    load_secrets()
    key = (explicit or os.environ.get("MISTRAL_API_KEY") or os.environ.get("MISTRALAI_API_KEY") or "").strip()
    if not key or key == DUMMY_KEY:
        raise MistralConfigError(
            "MistralAI engine needs MISTRAL_API_KEY in the environment or a local SECRETS.txt "
            "(https://console.mistral.ai/api-keys). Local PyMuPDF+Tesseract does not need a key."
        )
    return key


def _env_int(name: str, default: int = 0) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def parse_ocr_pages(payload: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    pages_in = payload.get("pages") or []
    pages: list[str] = []
    for item in pages_in:
        markdown = (item or {}).get("markdown") or ""
        pages.append(markdown.strip())
    usage = payload.get("usage_info") or {}
    meta = {
        "model": payload.get("model") or OCR_MODEL,
        "pages_processed": usage.get("pages_processed", len(pages)),
        "doc_size_bytes": usage.get("doc_size_bytes"),
        "usage_info": usage,
    }
    return pages, meta


def _json_request(
    method: str,
    url: str,
    api_key: str,
    *,
    body: dict | None = None,
    timeout: int = DEFAULT_TIMEOUT_S,
) -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        raise RuntimeError(f"MistralAI {method} {url} failed HTTP {exc.code}: {detail[:800]}") from exc
    except URLError as exc:
        raise RuntimeError(f"MistralAI {method} {url} network error: {exc.reason}") from exc
    return json.loads(raw) if raw else {}


def _multipart_upload(url: str, api_key: str, filename: str, content: bytes, timeout: int) -> dict:
    boundary = "----SlipMistral" + uuid.uuid4().hex
    crlf = b"\r\n"
    chunks = [
        f"--{boundary}".encode("ascii") + crlf,
        b'Content-Disposition: form-data; name="purpose"' + crlf + crlf,
        b"ocr" + crlf,
        f"--{boundary}".encode("ascii") + crlf,
        (
            f'Content-Disposition: form-data; name="file"; filename="{filename}"'
        ).encode()
        + crlf,
        b"Content-Type: application/pdf" + crlf + crlf,
        content,
        crlf,
        f"--{boundary}--".encode("ascii") + crlf,
    ]
    body = b"".join(chunks)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    req = Request(url, data=body, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        raise RuntimeError(f"MistralAI upload failed HTTP {exc.code}: {detail[:800]}") from exc
    except URLError as exc:
        raise RuntimeError(f"MistralAI upload network error: {exc.reason}") from exc
    return json.loads(raw) if raw else {}


Transport = Callable[..., dict]


class MistralOcrEngine:
    """Obsidian OCR-AI equivalent: upload PDF, OCR, optional delete."""

    name = "mistral"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        include_images: bool | None = None,
        image_limit: int | None = None,
        image_min_size: int | None = None,
        delete_upload: bool | None = None,
        timeout_s: int = DEFAULT_TIMEOUT_S,
        transport: Transport | None = None,
    ) -> None:
        self._explicit_key = api_key
        self.include_images = (
            _env_bool("SLIP_MISTRAL_INCLUDE_IMAGES", False)
            if include_images is None
            else include_images
        )
        self.image_limit = image_limit if image_limit is not None else _env_int("SLIP_MISTRAL_IMAGE_LIMIT", 0)
        self.image_min_size = (
            image_min_size if image_min_size is not None else _env_int("SLIP_MISTRAL_IMAGE_MIN_SIZE", 0)
        )
        # Law-firm default: delete the upload after OCR (plugin default is keep).
        self.delete_upload = (
            _env_bool("SLIP_MISTRAL_DELETE_UPLOAD", True)
            if delete_upload is None
            else delete_upload
        )
        self.timeout_s = timeout_s
        self.transport = transport

    def convert(self, pdf_path: Path) -> ConversionResult:
        pdf_path = Path(pdf_path)
        api_key = resolve_api_key(self._explicit_key)
        content = pdf_path.read_bytes()
        if not content:
            return ConversionResult(
                pages=[],
                page_count=0,
                engine=self.name,
                warnings=["empty PDF"],
                needs_review=True,
            )

        uploaded_id: str | None = None
        warnings: list[str] = [
            "PDF uploaded to Mistral servers for OCR; files may be stored at least 24 hours unless deleted"
        ]
        cb = getattr(self, "on_progress", None)
        try:
            if cb:
                cb(0.08, "uploading PDF to Mistral")
            upload = self._call(
                "upload",
                "POST",
                f"{API_ROOT}/v1/files",
                api_key,
                filename=pdf_path.name,
                content=content,
            )
            uploaded_id = str(upload.get("id") or "")
            if not uploaded_id:
                raise RuntimeError("MistralAI file upload returned no id")

            signed = self._call(
                "signed_url",
                "GET",
                f"{API_ROOT}/v1/files/{uploaded_id}/url?{urlencode({'expiry': 24})}",
                api_key,
            )
            document_url = signed.get("url")
            if not document_url:
                raise RuntimeError("MistralAI signed URL missing")

            ocr_body: dict[str, Any] = {
                "model": OCR_MODEL,
                "document": {"type": "document_url", "document_url": document_url},
                "include_image_base64": bool(self.include_images),
            }
            if self.image_limit > 0:
                ocr_body["image_limit"] = self.image_limit
            if self.image_min_size > 0:
                ocr_body["image_min_size"] = self.image_min_size

            if cb:
                cb(0.35, "Mistral OCR running")
            ocr = self._call("ocr", "POST", f"{API_ROOT}/v1/ocr", api_key, json_body=ocr_body)
            pages, meta = parse_ocr_pages(ocr)
            if cb:
                cb(0.90, f"received {len(pages)} page(s)")
            nonempty = sum(1 for p in pages if p.strip())
            usage = {
                "mistral_pages_processed": meta.get("pages_processed"),
                "mistral_doc_size_bytes": meta.get("doc_size_bytes"),
                "mistral_model": meta.get("model"),
                "llm_input_tokens": 0,
                "llm_output_tokens": 0,
            }
            return ConversionResult(
                pages=pages,
                page_count=len(pages),
                engine=self.name,
                warnings=warnings,
                needs_review=len(pages) == 0 or nonempty == 0,
                usage=usage,
            )
        except MistralConfigError:
            raise
        except Exception as exc:
            return ConversionResult(
                pages=[],
                page_count=0,
                engine=self.name,
                warnings=warnings + [str(exc)],
                needs_review=True,
            )
        finally:
            if self.delete_upload and uploaded_id:
                try:
                    self._call(
                        "delete",
                        "DELETE",
                        f"{API_ROOT}/v1/files/{uploaded_id}",
                        api_key,
                    )
                except Exception as cleanup_exc:
                    warnings.append(f"could not delete Mistral upload {uploaded_id}: {cleanup_exc}")

    def _call(self, op: str, method: str, url: str, api_key: str, **kwargs) -> dict:
        if self.transport is not None:
            return self.transport(op, method, url, api_key, **kwargs)
        if op == "upload":
            return _multipart_upload(
                url,
                api_key,
                kwargs["filename"],
                kwargs["content"],
                self.timeout_s,
            )
        return _json_request(
            method,
            url,
            api_key,
            body=kwargs.get("json_body"),
            timeout=self.timeout_s,
        )

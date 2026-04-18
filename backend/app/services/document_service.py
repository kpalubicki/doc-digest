import uuid
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import aiofiles
from pypdf import PdfReader

from app.config import settings


SUPPORTED_TYPES = {".pdf", ".txt", ".md"}
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
META_FILE = "meta.json"


def _load_meta() -> dict:
    meta_path = Path(settings.upload_path) / META_FILE
    if meta_path.exists():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    return {}


def _save_meta(meta: dict):
    meta_path = Path(settings.upload_path) / META_FILE
    tmp_path = meta_path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    tmp_path.replace(meta_path)  # atomic on POSIX, best-effort on Windows


def _extract_text(file_path: Path, suffix: str) -> str:
    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return file_path.read_text(encoding="utf-8", errors="ignore")


def _chunk_text(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end].strip())
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if len(c) > 50]


async def save_and_parse(filename: str, data: bytes) -> tuple[str, list[str], str]:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_TYPES:
        raise ValueError(f"Unsupported file type: {suffix}. Use PDF, TXT, or MD.")

    doc_id = str(uuid.uuid4())[:8]
    upload_dir = Path(settings.upload_path)
    file_path = upload_dir / f"{doc_id}{suffix}"

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(data)

    text = _extract_text(file_path, suffix)
    chunks = _chunk_text(text)

    meta = _load_meta()
    meta[doc_id] = {
        "filename": filename,
        "file_type": suffix,
        "chunk_count": len(chunks),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "tags": [],
    }
    _save_meta(meta)

    return doc_id, chunks, filename


def get_document(doc_id: str) -> Optional[dict]:
    meta = _load_meta()
    if doc_id not in meta:
        return None
    return {"id": doc_id, **meta[doc_id]}


def get_document_text(doc_id: str) -> str | None:
    """Return full extracted text for a document, or None if not found."""
    meta = _load_meta()
    if doc_id not in meta:
        return None
    suffix = meta[doc_id]["file_type"]
    file_path = Path(settings.upload_path) / f"{doc_id}{suffix}"
    if not file_path.exists():
        return None
    return _extract_text(file_path, suffix)


def set_tags(doc_id: str, tags: list[str]) -> bool:
    """Replace the tag list for a document. Returns False if not found."""
    meta = _load_meta()
    if doc_id not in meta:
        return False
    meta[doc_id]["tags"] = sorted(set(t.strip().lower() for t in tags if t.strip()))
    _save_meta(meta)
    return True


def list_documents(tag: str | None = None) -> list[dict]:
    meta = _load_meta()
    docs = [{"id": doc_id, **info} for doc_id, info in meta.items()]
    if tag:
        tag = tag.strip().lower()
        docs = [d for d in docs if tag in d.get("tags", [])]
    return docs


def delete_document(doc_id: str) -> bool:
    meta = _load_meta()
    if doc_id not in meta:
        return False

    suffix = meta[doc_id]["file_type"]
    file_path = Path(settings.upload_path) / f"{doc_id}{suffix}"
    if file_path.exists():
        file_path.unlink()

    del meta[doc_id]
    _save_meta(meta)
    return True

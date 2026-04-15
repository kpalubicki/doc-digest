"""Collections management endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.services import vector_store

router = APIRouter()


class CollectionListResponse(BaseModel):
    collections: list[str]
    count: int


class CollectionCreateRequest(BaseModel):
    name: str


class CollectionCreateResponse(BaseModel):
    name: str
    message: str


@router.get("", response_model=CollectionListResponse)
def list_collections() -> CollectionListResponse:
    """List all knowledge base collections."""
    names = vector_store.list_collections()
    return CollectionListResponse(collections=names, count=len(names))


@router.post("", response_model=CollectionCreateResponse)
def create_collection(request: CollectionCreateRequest) -> CollectionCreateResponse:
    """Create a new named collection (knowledge base)."""
    name = request.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Collection name cannot be empty.")
    # get_or_create — calling _get_collection creates it
    vector_store._get_collection(name)
    return CollectionCreateResponse(name=name, message=f"Collection '{name}' ready.")


@router.get("/{name}/export/markdown")
def export_collection_markdown(name: str) -> Response:
    """Export all document chunks in a collection as a single Markdown file.

    Chunks are grouped by source document and ordered by position.
    Returns 404 if the collection does not exist or is empty.
    """
    chunks_by_file = vector_store.get_collection_chunks(name)
    if not chunks_by_file:
        raise HTTPException(
            status_code=404,
            detail=f"Collection '{name}' not found or contains no documents.",
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = [
        f"# Collection: {name}",
        "",
        f"*Exported {timestamp} — {len(chunks_by_file)} document(s)*",
        "",
    ]

    for filename, chunks in chunks_by_file.items():
        lines.append(f"## {filename}")
        lines.append("")
        for chunk in chunks:
            lines.append(chunk)
            lines.append("")
        lines.append("---")
        lines.append("")

    content = "\n".join(lines)
    slug = name.lower().replace(" ", "-")[:40]
    filename_out = f"{slug}.md"

    return Response(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename_out}"'},
    )


@router.delete("/{name}")
def delete_collection(name: str):
    """Delete a collection and all its documents."""
    deleted = vector_store.delete_collection(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found.")
    return {"name": name, "message": f"Collection '{name}' deleted."}

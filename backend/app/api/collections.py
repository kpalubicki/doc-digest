"""Collections management endpoints."""

from fastapi import APIRouter, HTTPException
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


@router.delete("/{name}")
def delete_collection(name: str):
    """Delete a collection and all its documents."""
    deleted = vector_store.delete_collection(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found.")
    return {"name": name, "message": f"Collection '{name}' deleted."}

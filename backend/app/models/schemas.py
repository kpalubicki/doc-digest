from pydantic import BaseModel
from typing import Optional


class DocumentInfo(BaseModel):
    id: str
    filename: str
    file_type: str
    chunk_count: int
    uploaded_at: str


class DocumentList(BaseModel):
    documents: list[DocumentInfo]
    count: int


class DeleteResponse(BaseModel):
    message: str


class ChatRequest(BaseModel):
    question: str
    document_id: Optional[str] = None  # None = search across all docs
    n_results: int = 4


class Source(BaseModel):
    document_id: str
    filename: str
    chunk: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]

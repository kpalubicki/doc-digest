from pydantic import BaseModel
from typing import Optional


class DocumentInfo(BaseModel):
    id: str
    filename: str
    file_type: str
    chunk_count: int
    uploaded_at: str
    tags: list[str] = []


class DocumentList(BaseModel):
    documents: list[DocumentInfo]
    count: int


class DeleteResponse(BaseModel):
    message: str


class ChatRequest(BaseModel):
    question: str
    document_id: Optional[str] = None  # None = search across all docs
    n_results: int = 4
    collection: str = "default"
    rerank: bool = False


class Source(BaseModel):
    document_id: str
    filename: str
    chunk: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]


class TagsRequest(BaseModel):
    tags: list[str]


class RerankRequest(BaseModel):
    question: str
    chunks: list[str]
    top_n: int = 4


class SummarizeRequest(BaseModel):
    style: str = "concise"  # concise | detailed | bullet-points


class SummarizeResponse(BaseModel):
    document_id: str
    filename: str
    summary: str
    model: str


class ConversationMessage(BaseModel):
    question: str
    answer: str
    sources: list[Source] = []


class ConversationExportRequest(BaseModel):
    messages: list[ConversationMessage]
    title: Optional[str] = None
    collection: Optional[str] = None

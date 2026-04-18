from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import DocumentInfo, DocumentList, DeleteResponse, SummarizeRequest, SummarizeResponse, TagsRequest
from app.services import chat_service, document_service, vector_store
from app.services.document_service import set_tags
from app.services.vector_store import DEFAULT_COLLECTION

router = APIRouter()


@router.post("", response_model=DocumentInfo)
async def upload_document(
    file: UploadFile = File(...),
    collection: str = Form(default=DEFAULT_COLLECTION),
):
    data = await file.read()
    try:
        doc_id, chunks, filename = await document_service.save_and_parse(file.filename, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    vector_store.add_chunks(doc_id, filename, chunks, collection_name=collection)

    doc = document_service.get_document(doc_id)
    return DocumentInfo(**doc)


@router.get("", response_model=DocumentList)
def list_documents(tag: str | None = None):
    docs = document_service.list_documents(tag=tag)
    return DocumentList(
        documents=[DocumentInfo(**d) for d in docs],
        count=len(docs),
    )


@router.get("/{doc_id}", response_model=DocumentInfo)
def get_document(doc_id: str):
    doc = document_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentInfo(**doc)


@router.post("/{doc_id}/summarize", response_model=SummarizeResponse)
def summarize_document(doc_id: str, request: SummarizeRequest = SummarizeRequest()) -> SummarizeResponse:
    """Summarize a document. style: concise | detailed | bullet-points"""
    doc = document_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    text = document_service.get_document_text(doc_id)
    if not text:
        raise HTTPException(status_code=404, detail="Document file not found")
    try:
        return chat_service.summarize(doc_id, doc["filename"], text, style=request.style)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Model error: {e}") from e


@router.post("/{doc_id}/summarize/stream")
def summarize_document_stream(doc_id: str, request: SummarizeRequest = SummarizeRequest()) -> StreamingResponse:
    """Stream document summary token by token as SSE."""
    doc = document_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    text = document_service.get_document_text(doc_id)
    if not text:
        raise HTTPException(status_code=404, detail="Document file not found")
    return StreamingResponse(
        chat_service.summarize_stream(doc_id, doc["filename"], text, style=request.style),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.put("/{doc_id}/tags", response_model=DocumentInfo)
def update_document_tags(doc_id: str, body: TagsRequest):
    """Replace the tags on a document."""
    doc = document_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    set_tags(doc_id, body.tags)
    return DocumentInfo(**document_service.get_document(doc_id))


@router.delete("/{doc_id}", response_model=DeleteResponse)
def delete_document(doc_id: str, collection: str = DEFAULT_COLLECTION):
    vector_store.delete_chunks(doc_id, collection_name=collection)
    deleted = document_service.delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return DeleteResponse(message=f"Document {doc_id} deleted")

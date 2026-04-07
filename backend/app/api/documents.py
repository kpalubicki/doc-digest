from fastapi import APIRouter, Form, UploadFile, File, HTTPException

from app.models.schemas import DocumentInfo, DocumentList, DeleteResponse
from app.services import document_service, vector_store
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
def list_documents():
    docs = document_service.list_documents()
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


@router.delete("/{doc_id}", response_model=DeleteResponse)
def delete_document(doc_id: str, collection: str = DEFAULT_COLLECTION):
    vector_store.delete_chunks(doc_id, collection_name=collection)
    deleted = document_service.delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return DeleteResponse(message=f"Document {doc_id} deleted")

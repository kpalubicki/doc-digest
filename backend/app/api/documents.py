from fastapi import APIRouter, UploadFile, File, HTTPException

from app.models.schemas import DocumentInfo, DocumentList, DeleteResponse
from app.services import document_service, vector_store

router = APIRouter()


@router.post("", response_model=DocumentInfo)
async def upload_document(file: UploadFile = File(...)):
    data = await file.read()
    try:
        doc_id, chunks, filename = await document_service.save_and_parse(file.filename, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    vector_store.add_chunks(doc_id, filename, chunks)

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
def delete_document(doc_id: str):
    vector_store.delete_chunks(doc_id)
    deleted = document_service.delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return DeleteResponse(message=f"Document {doc_id} deleted")

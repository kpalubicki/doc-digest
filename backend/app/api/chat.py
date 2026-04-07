from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest, ChatResponse
from app.services import chat_service

router = APIRouter()


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    return chat_service.ask(
        question=request.question,
        doc_id=request.document_id,
        n_results=request.n_results,
        collection_name=request.collection,
    )


@router.post("/stream")
def chat_stream(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    return StreamingResponse(
        chat_service.ask_stream(
            question=request.question,
            doc_id=request.document_id,
            n_results=request.n_results,
            collection_name=request.collection,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

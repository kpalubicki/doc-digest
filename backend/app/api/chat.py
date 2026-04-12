from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse

from app.models.schemas import ChatRequest, ChatResponse, ConversationExportRequest
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


@router.post("/export/markdown")
def export_markdown(request: ConversationExportRequest) -> Response:
    """Export a conversation (list of Q&A messages) as a Markdown file.

    The client holds the conversation and POSTs it here; no server-side history required.
    Returns a downloadable .md file.
    """
    if not request.messages:
        raise HTTPException(status_code=422, detail="No messages to export.")

    title = request.title or "Conversation"
    collection_line = f"**Collection:** {request.collection}\n\n" if request.collection else ""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines: list[str] = [
        f"# {title}",
        "",
        f"*Exported {timestamp}*",
        "",
    ]
    if collection_line:
        lines.append(collection_line)

    for i, msg in enumerate(request.messages, start=1):
        lines.append(f"## Q{i}: {msg.question}")
        lines.append("")
        lines.append(msg.answer)
        lines.append("")
        if msg.sources:
            lines.append("**Sources:**")
            for src in msg.sources:
                lines.append(f"- `{src.filename}`: {src.chunk[:120]}{'...' if len(src.chunk) > 120 else ''}")
            lines.append("")

    content = "\n".join(lines)
    slug = title.lower().replace(" ", "-")[:40]
    filename = f"{slug}.md"

    return Response(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

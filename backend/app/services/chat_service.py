import json
from typing import Generator

import ollama

from app.config import settings
from app.services.vector_store import search
from app.models.schemas import ChatResponse, Source


SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on provided document excerpts.
Answer only using the provided context. If the context doesn't contain enough information to answer, say so.
Be concise and direct."""


def _build_context(hits: list[dict]) -> str:
    return "\n\n---\n\n".join(
        f"[{h['filename']}]\n{h['chunk']}" for h in hits
    )


def _build_sources(hits: list[dict]) -> list[Source]:
    return [
        Source(
            document_id=h["doc_id"],
            filename=h["filename"],
            chunk=h["chunk"][:300] + ("..." if len(h["chunk"]) > 300 else ""),
        )
        for h in hits
    ]


def ask(question: str, doc_id: str | None = None, n_results: int = 4) -> ChatResponse:
    hits = search(question, doc_id=doc_id, n_results=n_results)

    if not hits:
        return ChatResponse(
            answer="No relevant content found in the uploaded documents.",
            sources=[],
        )

    context = _build_context(hits)
    prompt = f"Context from documents:\n\n{context}\n\nQuestion: {question}\n\nAnswer:"

    response = ollama.chat(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )

    return ChatResponse(answer=response.message.content.strip(), sources=_build_sources(hits))


def ask_stream(question: str, doc_id: str | None = None, n_results: int = 4) -> Generator[str, None, None]:
    """Stream answer token by token as SSE events, then emit sources as the final event."""
    hits = search(question, doc_id=doc_id, n_results=n_results)

    if not hits:
        yield f"data: {json.dumps({'token': 'No relevant content found in the uploaded documents.'})}\n\n"
        yield f"data: {json.dumps({'sources': [], 'done': True})}\n\n"
        return

    context = _build_context(hits)
    prompt = f"Context from documents:\n\n{context}\n\nQuestion: {question}\n\nAnswer:"

    stream = ollama.chat(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        stream=True,
    )

    for chunk in stream:
        token = chunk.message.content
        if token:
            yield f"data: {json.dumps({'token': token})}\n\n"

    sources = [s.model_dump() for s in _build_sources(hits)]
    yield f"data: {json.dumps({'sources': sources, 'done': True})}\n\n"

import json
from typing import Generator

import ollama

from app.config import settings
from app.services.vector_store import search, DEFAULT_COLLECTION
from app.models.schemas import ChatResponse, Source, SummarizeResponse


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


def ask(question: str, doc_id: str | None = None, n_results: int = 4,
        collection_name: str = DEFAULT_COLLECTION) -> ChatResponse:
    hits = search(question, doc_id=doc_id, n_results=n_results, collection_name=collection_name)

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


def ask_stream(question: str, doc_id: str | None = None, n_results: int = 4,
               collection_name: str = DEFAULT_COLLECTION) -> Generator[str, None, None]:
    """Stream answer token by token as SSE events, then emit sources as the final event."""
    hits = search(question, doc_id=doc_id, n_results=n_results, collection_name=collection_name)

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


_STYLE_INSTRUCTION = {
    "concise": "Write a concise 2-4 sentence summary capturing the key points.",
    "detailed": "Write a detailed summary covering the main topics, arguments, and conclusions.",
    "bullet-points": "Summarize as a Markdown bullet-point list of the key points.",
}


def summarize(doc_id: str, filename: str, text: str, style: str = "concise") -> SummarizeResponse:
    """Summarize document text using Ollama."""
    instruction = _STYLE_INSTRUCTION.get(style, _STYLE_INSTRUCTION["concise"])
    prompt = f"Document:\n\n{text[:8000]}\n\n{instruction}"

    response = ollama.chat(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes documents accurately."},
            {"role": "user", "content": prompt},
        ],
    )

    return SummarizeResponse(
        document_id=doc_id,
        filename=filename,
        summary=response.message.content.strip(),
        model=settings.chat_model,
    )


def summarize_stream(doc_id: str, filename: str, text: str, style: str = "concise") -> Generator[str, None, None]:
    """Stream document summary token by token as SSE events."""
    instruction = _STYLE_INSTRUCTION.get(style, _STYLE_INSTRUCTION["concise"])
    prompt = f"Document:\n\n{text[:8000]}\n\n{instruction}"

    stream = ollama.chat(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes documents accurately."},
            {"role": "user", "content": prompt},
        ],
        stream=True,
    )

    for chunk in stream:
        token = chunk.message.content
        if token:
            yield f"data: {json.dumps({'token': token})}\n\n"

    yield f"data: {json.dumps({'done': True, 'document_id': doc_id, 'model': settings.chat_model})}\n\n"

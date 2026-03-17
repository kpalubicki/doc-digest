import ollama

from app.config import settings
from app.services.vector_store import search
from app.models.schemas import ChatResponse, Source


SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on provided document excerpts.
Answer only using the provided context. If the context doesn't contain enough information to answer, say so.
Be concise and direct."""


def ask(question: str, doc_id: str | None = None, n_results: int = 4) -> ChatResponse:
    hits = search(question, doc_id=doc_id, n_results=n_results)

    if not hits:
        return ChatResponse(
            answer="No relevant content found in the uploaded documents.",
            sources=[],
        )

    context = "\n\n---\n\n".join(
        f"[{h['filename']}]\n{h['chunk']}" for h in hits
    )

    prompt = f"""Context from documents:

{context}

Question: {question}

Answer:"""

    response = ollama.chat(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )

    answer = response.message.content.strip()

    sources = [
        Source(
            document_id=h["doc_id"],
            filename=h["filename"],
            chunk=h["chunk"][:300] + ("..." if len(h["chunk"]) > 300 else ""),
        )
        for h in hits
    ]

    return ChatResponse(answer=answer, sources=sources)

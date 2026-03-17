import chromadb
from chromadb.config import Settings as ChromaSettings
import ollama

from app.config import settings

_client: chromadb.ClientAPI | None = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        _collection = _client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _embed(texts: list[str]) -> list[list[float]]:
    response = ollama.embed(model=settings.embed_model, input=texts)
    return response.embeddings


def add_chunks(doc_id: str, filename: str, chunks: list[str]):
    collection = _get_collection()
    embeddings = _embed(chunks)
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    metadatas = [{"doc_id": doc_id, "filename": filename, "chunk_index": i} for i in range(len(chunks))]
    collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)


def search(query: str, doc_id: str | None = None, n_results: int = 4) -> list[dict]:
    collection = _get_collection()
    where = {"doc_id": doc_id} if doc_id else None
    query_embedding = _embed([query])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({
            "chunk": doc,
            "doc_id": meta["doc_id"],
            "filename": meta["filename"],
            "score": 1 - dist,
        })
    return hits


def delete_chunks(doc_id: str):
    collection = _get_collection()
    existing = collection.get(where={"doc_id": doc_id})
    if existing["ids"]:
        collection.delete(ids=existing["ids"])

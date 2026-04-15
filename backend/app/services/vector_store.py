import chromadb
from chromadb.config import Settings as ChromaSettings
import ollama

from app.config import settings

DEFAULT_COLLECTION = "default"

_client: chromadb.ClientAPI | None = None


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def _get_collection(collection_name: str = DEFAULT_COLLECTION):
    client = _get_client()
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def _embed(texts: list[str]) -> list[list[float]]:
    response = ollama.embed(model=settings.embed_model, input=texts)
    return response.embeddings


def list_collections() -> list[str]:
    """Return names of all existing collections."""
    return [c.name for c in _get_client().list_collections()]


def delete_collection(collection_name: str) -> bool:
    """Delete an entire collection. Returns False if it didn't exist."""
    client = _get_client()
    existing = [c.name for c in client.list_collections()]
    if collection_name not in existing:
        return False
    client.delete_collection(collection_name)
    return True


def add_chunks(doc_id: str, filename: str, chunks: list[str],
               collection_name: str = DEFAULT_COLLECTION):
    collection = _get_collection(collection_name)
    embeddings = _embed(chunks)
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    metadatas = [{"doc_id": doc_id, "filename": filename, "chunk_index": i}
                 for i in range(len(chunks))]
    collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)


def search(query: str, doc_id: str | None = None, n_results: int = 4,
           collection_name: str = DEFAULT_COLLECTION) -> list[dict]:
    collection = _get_collection(collection_name)
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


def delete_chunks(doc_id: str, collection_name: str = DEFAULT_COLLECTION):
    collection = _get_collection(collection_name)
    existing = collection.get(where={"doc_id": doc_id})
    if existing["ids"]:
        collection.delete(ids=existing["ids"])


def get_collection_chunks(collection_name: str = DEFAULT_COLLECTION) -> dict[str, list[str]]:
    """Return all chunks in a collection grouped by filename.

    Returns {filename: [chunk, ...]} ordered by chunk_index.
    Returns an empty dict if the collection doesn't exist or has no documents.
    """
    client = _get_client()
    existing = [c.name for c in client.list_collections()]
    if collection_name not in existing:
        return {}

    collection = _get_collection(collection_name)
    result = collection.get(include=["documents", "metadatas"])
    if not result["ids"]:
        return {}

    # Group chunks by filename, sorted by chunk_index
    from collections import defaultdict
    grouped: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for doc, meta in zip(result["documents"], result["metadatas"]):
        filename = meta.get("filename", "unknown")
        chunk_index = meta.get("chunk_index", 0)
        grouped[filename].append((chunk_index, doc))

    return {
        filename: [chunk for _, chunk in sorted(chunks)]
        for filename, chunks in grouped.items()
    }

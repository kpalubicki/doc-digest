"""Tests for /collections endpoints and multi-collection vector_store behavior."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app

client = TestClient(app)


# --- /collections endpoints ---

def test_list_collections_empty():
    with patch("app.api.collections.vector_store.list_collections", return_value=[]):
        r = client.get("/collections")
    assert r.status_code == 200
    data = r.json()
    assert data["collections"] == []
    assert data["count"] == 0


def test_list_collections_returns_names():
    with patch("app.api.collections.vector_store.list_collections", return_value=["default", "legal"]):
        r = client.get("/collections")
    assert r.status_code == 200
    data = r.json()
    assert data["collections"] == ["default", "legal"]
    assert data["count"] == 2


def test_create_collection():
    with patch("app.api.collections.vector_store._get_collection") as mock_get:
        r = client.post("/collections", json={"name": "legal"})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "legal"
    mock_get.assert_called_once_with("legal")


def test_create_collection_empty_name():
    r = client.post("/collections", json={"name": "   "})
    assert r.status_code == 422


def test_delete_collection_success():
    with patch("app.api.collections.vector_store.delete_collection", return_value=True):
        r = client.delete("/collections/legal")
    assert r.status_code == 200
    assert r.json()["name"] == "legal"


def test_delete_collection_not_found():
    with patch("app.api.collections.vector_store.delete_collection", return_value=False):
        r = client.delete("/collections/nonexistent")
    assert r.status_code == 404


# --- multi-collection routing in chat ---

def test_chat_passes_collection_to_service():
    fake_response = MagicMock()
    fake_response.answer = "Answer from legal collection."
    fake_response.sources = []

    with patch("app.api.chat.chat_service.ask", return_value=fake_response) as mock_ask:
        r = client.post("/chat", json={"question": "what is the law?", "collection": "legal"})

    assert r.status_code == 200
    mock_ask.assert_called_once_with(
        question="what is the law?",
        doc_id=None,
        n_results=4,
        collection_name="legal",
        use_rerank=False,
    )


def test_chat_defaults_to_default_collection():
    fake_response = MagicMock()
    fake_response.answer = "Answer."
    fake_response.sources = []

    with patch("app.api.chat.chat_service.ask", return_value=fake_response) as mock_ask:
        r = client.post("/chat", json={"question": "hello?"})

    assert r.status_code == 200
    mock_ask.assert_called_once_with(
        question="hello?",
        doc_id=None,
        n_results=4,
        collection_name="default",
        use_rerank=False,
    )


# --- upload document to named collection ---

def test_upload_to_named_collection():
    fake_doc = {
        "id": "abc", "filename": "law.pdf", "file_type": ".pdf",
        "chunk_count": 3, "uploaded_at": "2026-01-01",
    }
    with patch("app.api.documents.document_service.save_and_parse",
               return_value=("abc", ["chunk1", "chunk2", "chunk3"], "law.pdf")):
        with patch("app.api.documents.vector_store.add_chunks") as mock_add:
            with patch("app.api.documents.document_service.get_document", return_value=fake_doc):
                r = client.post(
                    "/documents",
                    files={"file": ("law.pdf", b"%PDF-1.4 content", "application/pdf")},
                    data={"collection": "legal"},
                )
    assert r.status_code == 200
    mock_add.assert_called_once_with("abc", "law.pdf", ["chunk1", "chunk2", "chunk3"], collection_name="legal")


# --- vector_store multi-collection unit tests ---

def test_vector_store_search_uses_collection():
    from app.services import vector_store

    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "documents": [["chunk text"]],
        "metadatas": [[{"doc_id": "d1", "filename": "f.pdf"}]],
        "distances": [[0.1]],
    }

    with patch.object(vector_store, "_get_collection", return_value=mock_collection) as mock_get:
        with patch.object(vector_store, "_embed", return_value=[[0.1, 0.2]]):
            hits = vector_store.search("query", collection_name="legal", n_results=2)

    mock_get.assert_called_once_with("legal")
    assert len(hits) == 1
    assert hits[0]["doc_id"] == "d1"


def test_vector_store_add_chunks_uses_collection():
    from app.services import vector_store

    mock_collection = MagicMock()

    with patch.object(vector_store, "_get_collection", return_value=mock_collection) as mock_get:
        with patch.object(vector_store, "_embed", return_value=[[0.1, 0.2]]):
            vector_store.add_chunks("doc1", "file.txt", ["chunk"], collection_name="tech")

    mock_get.assert_called_once_with("tech")
    mock_collection.add.assert_called_once()


def test_vector_store_delete_collection_not_found():
    from app.services import vector_store

    mock_client = MagicMock()
    mock_client.list_collections.return_value = []

    with patch.object(vector_store, "_get_client", return_value=mock_client):
        result = vector_store.delete_collection("ghost")

    assert result is False


def test_vector_store_delete_collection_success():
    from app.services import vector_store

    mock_col = MagicMock()
    mock_col.name = "legal"
    mock_client = MagicMock()
    mock_client.list_collections.return_value = [mock_col]

    with patch.object(vector_store, "_get_client", return_value=mock_client):
        result = vector_store.delete_collection("legal")

    assert result is True
    mock_client.delete_collection.assert_called_once_with("legal")


# --- /collections/{name}/export/markdown tests ---

def test_export_collection_markdown_not_found():
    with patch("app.api.collections.vector_store.get_collection_chunks", return_value={}):
        r = client.get("/collections/ghost/export/markdown")
    assert r.status_code == 404


def test_export_collection_markdown_returns_file():
    chunks = {
        "report.pdf": ["Introduction text.", "Main findings here."],
        "notes.txt": ["Quick notes from the meeting."],
    }
    with patch("app.api.collections.vector_store.get_collection_chunks", return_value=chunks):
        r = client.get("/collections/research/export/markdown")
    assert r.status_code == 200
    assert "text/markdown" in r.headers["content-type"]
    assert "research.md" in r.headers["content-disposition"]


def test_export_collection_markdown_contains_docs():
    chunks = {
        "report.pdf": ["First chunk.", "Second chunk."],
    }
    with patch("app.api.collections.vector_store.get_collection_chunks", return_value=chunks):
        r = client.get("/collections/research/export/markdown")
    text = r.text
    assert "# Collection: research" in text
    assert "## report.pdf" in text
    assert "First chunk." in text
    assert "Second chunk." in text


def test_export_collection_markdown_multiple_docs():
    chunks = {
        "a.pdf": ["chunk a"],
        "b.txt": ["chunk b"],
    }
    with patch("app.api.collections.vector_store.get_collection_chunks", return_value=chunks):
        r = client.get("/collections/research/export/markdown")
    text = r.text
    assert "## a.pdf" in text
    assert "## b.txt" in text
    assert "chunk a" in text
    assert "chunk b" in text


def test_vector_store_get_collection_chunks_unknown_collection():
    from app.services import vector_store

    mock_client = MagicMock()
    mock_client.list_collections.return_value = []

    with patch.object(vector_store, "_get_client", return_value=mock_client):
        result = vector_store.get_collection_chunks("ghost")

    assert result == {}


def test_vector_store_get_collection_chunks_groups_by_filename():
    from app.services import vector_store

    mock_col = MagicMock()
    mock_col.name = "research"
    mock_client = MagicMock()
    mock_client.list_collections.return_value = [mock_col]

    mock_collection = MagicMock()
    mock_collection.get.return_value = {
        "ids": ["d1_0", "d1_1", "d2_0"],
        "documents": ["chunk A0", "chunk A1", "chunk B0"],
        "metadatas": [
            {"filename": "a.pdf", "chunk_index": 0, "doc_id": "d1"},
            {"filename": "a.pdf", "chunk_index": 1, "doc_id": "d1"},
            {"filename": "b.txt", "chunk_index": 0, "doc_id": "d2"},
        ],
    }

    with patch.object(vector_store, "_get_client", return_value=mock_client):
        with patch.object(vector_store, "_get_collection", return_value=mock_collection):
            result = vector_store.get_collection_chunks("research")

    assert "a.pdf" in result
    assert "b.txt" in result
    assert result["a.pdf"] == ["chunk A0", "chunk A1"]
    assert result["b.txt"] == ["chunk B0"]

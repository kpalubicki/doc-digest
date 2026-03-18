"""Integration tests for the FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import io

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model" in data


def test_list_documents_empty(tmp_path):
    with patch("app.api.documents.document_service.list_documents", return_value=[]):
        response = client.get("/documents")
        assert response.status_code == 200
        assert response.json()["documents"] == []


def test_list_documents_returns_data(tmp_path):
    fake_docs = [
        {"id": "abc123", "filename": "test.pdf", "file_type": ".pdf", "chunk_count": 5, "uploaded_at": "2025-01-01"}
    ]
    with patch("app.api.documents.document_service.list_documents", return_value=fake_docs):
        response = client.get("/documents")
        assert response.status_code == 200
        assert len(response.json()["documents"]) == 1
        assert response.json()["documents"][0]["filename"] == "test.pdf"


def test_upload_unsupported_file_type():
    data = {"file": ("script.js", b"console.log('hi')", "text/javascript")}
    response = client.post("/documents", files=data)
    assert response.status_code == 400
    assert "Unsupported" in response.json()["detail"]


def test_delete_document_not_found():
    with patch("app.api.documents.document_service.delete_document", return_value=False):
        with patch("app.api.documents.vector_store.delete_chunks"):
            response = client.delete("/documents/nonexistent")
            assert response.status_code == 404


def test_chat_requires_question():
    response = client.post("/chat", json={})
    assert response.status_code == 422


def test_chat_empty_question():
    response = client.post("/chat", json={"question": "   "})
    assert response.status_code == 400


def test_chat_returns_answer():
    fake_response = MagicMock()
    fake_response.answer = "The document says hello."
    fake_response.sources = []

    with patch("app.api.chat.chat_service.ask", return_value=fake_response):
        response = client.post("/chat", json={"question": "what does it say?"})
        assert response.status_code == 200
        assert "answer" in response.json()

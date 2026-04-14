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


# --- /documents/{id}/summarize tests ---

FAKE_DOC = {"id": "abc123", "filename": "report.txt", "file_type": ".txt", "chunk_count": 5, "uploaded_at": "2026-01-01"}
FAKE_SUMMARY_RESPONSE = MagicMock(
    document_id="abc123",
    filename="report.txt",
    summary="This document discusses key findings.",
    model="qwen2.5:3b",
)


def test_summarize_returns_summary():
    with patch("app.api.documents.document_service.get_document", return_value=FAKE_DOC), \
         patch("app.api.documents.document_service.get_document_text", return_value="Some document text."), \
         patch("app.api.documents.chat_service.summarize", return_value=FAKE_SUMMARY_RESPONSE):
        r = client.post("/documents/abc123/summarize", json={})
    assert r.status_code == 200
    data = r.json()
    assert data["document_id"] == "abc123"
    assert data["summary"] == "This document discusses key findings."
    assert data["model"] == "qwen2.5:3b"


def test_summarize_not_found():
    with patch("app.api.documents.document_service.get_document", return_value=None):
        r = client.post("/documents/missing/summarize", json={})
    assert r.status_code == 404


def test_summarize_file_missing():
    with patch("app.api.documents.document_service.get_document", return_value=FAKE_DOC), \
         patch("app.api.documents.document_service.get_document_text", return_value=None):
        r = client.post("/documents/abc123/summarize", json={})
    assert r.status_code == 404


def test_summarize_model_error():
    with patch("app.api.documents.document_service.get_document", return_value=FAKE_DOC), \
         patch("app.api.documents.document_service.get_document_text", return_value="text"), \
         patch("app.api.documents.chat_service.summarize", side_effect=RuntimeError("model offline")):
        r = client.post("/documents/abc123/summarize", json={})
    assert r.status_code == 502
    assert "model offline" in r.json()["detail"]


def test_summarize_custom_style():
    called_with = {}

    def capture_summarize(doc_id, filename, text, style="concise"):
        called_with["style"] = style
        return FAKE_SUMMARY_RESPONSE

    with patch("app.api.documents.document_service.get_document", return_value=FAKE_DOC), \
         patch("app.api.documents.document_service.get_document_text", return_value="text"), \
         patch("app.api.documents.chat_service.summarize", side_effect=capture_summarize):
        client.post("/documents/abc123/summarize", json={"style": "bullet-points"})
    assert called_with["style"] == "bullet-points"


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


# --- API key auth tests ---

def test_no_auth_when_key_not_configured():
    # API_KEY unset → all requests pass through
    with patch("app.api.documents.document_service.list_documents", return_value=[]):
        r = client.get("/documents")
    assert r.status_code == 200


def test_rejects_request_without_key(monkeypatch):
    monkeypatch.setattr("app.api.auth.settings", type("S", (), {"api_key": "secret"})())
    with patch("app.api.documents.document_service.list_documents", return_value=[]):
        r = client.get("/documents")
    assert r.status_code == 401


def test_rejects_wrong_key(monkeypatch):
    monkeypatch.setattr("app.api.auth.settings", type("S", (), {"api_key": "secret"})())
    with patch("app.api.documents.document_service.list_documents", return_value=[]):
        r = client.get("/documents", headers={"X-API-Key": "wrong"})
    assert r.status_code == 401


def test_accepts_correct_key(monkeypatch):
    monkeypatch.setattr("app.api.auth.settings", type("S", (), {"api_key": "secret"})())
    with patch("app.api.documents.document_service.list_documents", return_value=[]):
        r = client.get("/documents", headers={"X-API-Key": "secret"})
    assert r.status_code == 200


def test_health_no_auth_required():
    # /health is public regardless of key config
    r = client.get("/health")
    assert r.status_code == 200


# --- /chat/export/markdown tests ---

EXPORT_MESSAGES = [
    {
        "question": "What is the capital of France?",
        "answer": "The capital of France is Paris.",
        "sources": [{"document_id": "abc", "filename": "geo.pdf", "chunk": "France is in Western Europe."}],
    },
    {
        "question": "How large is Paris?",
        "answer": "Paris has a population of about 2 million in the city proper.",
        "sources": [],
    },
]


def test_export_markdown_returns_file():
    r = client.post("/chat/export/markdown", json={"messages": EXPORT_MESSAGES})
    assert r.status_code == 200
    assert "text/markdown" in r.headers["content-type"]
    assert ".md" in r.headers["content-disposition"]


def test_export_markdown_contains_questions_and_answers():
    r = client.post("/chat/export/markdown", json={"messages": EXPORT_MESSAGES})
    text = r.text
    assert "What is the capital of France?" in text
    assert "The capital of France is Paris." in text
    assert "How large is Paris?" in text
    assert "2 million" in text


def test_export_markdown_contains_sources():
    r = client.post("/chat/export/markdown", json={"messages": EXPORT_MESSAGES})
    assert "geo.pdf" in r.text


def test_export_markdown_custom_title():
    r = client.post("/chat/export/markdown", json={"messages": EXPORT_MESSAGES, "title": "My Research"})
    assert "My Research" in r.text
    assert "my-research.md" in r.headers["content-disposition"]


def test_export_markdown_with_collection():
    r = client.post("/chat/export/markdown", json={
        "messages": EXPORT_MESSAGES,
        "collection": "geography",
    })
    assert "geography" in r.text


def test_export_markdown_empty_messages():
    r = client.post("/chat/export/markdown", json={"messages": []})
    assert r.status_code == 422


def test_export_markdown_no_messages_field():
    r = client.post("/chat/export/markdown", json={})
    assert r.status_code == 422

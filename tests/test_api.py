import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
import httpx
from google import genai
from httpx import TimeoutException

from app.config import ROOT
from app.services.generation import GenerationService


def upload(client, name="policy.txt", content=b"Customers may cancel their service at any time."):
    return client.post("/api/documents", files={"file": (name, content)})


def test_pages_and_health(client):
    for path in ["/", "/admin", "/docs", "/static/js/source.js"]:
        assert client.get(path).status_code == 200
    assert client.get("/api/health").json()["status"] == "ok"
    assert client.get("/api/ready").json()["ready"] is True
    assert client.get("/api/documents").json() == []


def test_upload_retrieve_chat_and_delete(client):
    response = upload(client)
    assert response.status_code == 201
    document = response.json()["document"]
    assert document["searchable"] is True

    response = client.post("/api/retrieve", json={"question": "Can I cancel?"})
    assert response.status_code == 200
    passage = response.json()["passages"][0]
    assert passage["document_id"] == document["document_id"]
    assert client.get(passage["passage_url"]).status_code == 200
    detail = client.get(f"/api/documents/{document['document_id']}/chunks/{passage['chunk_id']}").json()
    assert detail["page_text"][detail["char_start"]:detail["char_end"]] == passage["excerpt"]
    assert client.get(detail["source_url"]).status_code == 200

    response = client.post("/api/chat", json={"question": "Can I cancel?"})
    assert response.status_code == 200
    assert response.json()["sources"][0]["passage_url"] == passage["passage_url"]
    assert client.delete(f"/api/documents/{document['document_id']}").status_code == 204
    assert client.get("/api/documents").json() == []


def test_pdf_metadata_and_page_link(client):
    path = ROOT / "knowledge_base/pdf/customer_approved/01_Troubleshooting/Red_LOS_and_PON_Errors.pdf"
    response = upload(client, path.name, path.read_bytes())
    assert response.status_code == 201
    document = response.json()["document"]
    assert document["metadata"]["article_id"] == "NF-TS-002"
    passage = client.post("/api/retrieve", json={"question": "red LOS"}).json()["passages"][0]
    assert passage["metadata"]["version"] == "1.0"
    assert "#page=" in passage["source_url"]


def test_basic_invalid_requests_and_duplicates(client):
    assert upload(client, "unsupported.docx").status_code == 422
    assert upload(client, content=b"").status_code == 422
    assert client.post("/api/chat", json={"question": " "}).status_code == 422
    assert client.get(f"/api/documents/{uuid4()}/source").status_code == 404
    upload(client)
    assert upload(client).json()["duplicate"] is True
    assert len(client.get("/api/documents").json()) == 1


def test_empty_chat_and_not_ready(client):
    response = client.post("/api/chat", json={"question": "What is the policy?"})
    assert response.status_code == 200
    assert response.json()["status"] == "no_documents"
    client.app.state.rag.ready = False
    assert upload(client).status_code == 503


def test_chat_citation_cards(client):
    upload(client, "first.txt", b"First policy.")
    upload(client, "second.txt", b"Second policy.")
    generator = GenerationService("test-key", "test-model")
    payload = {"answer": "See both policies [S1, S2].", "source_ids": ["S1", "S2"]}
    generator.client = SimpleNamespace(
        models=SimpleNamespace(generate_content=lambda **kwargs: SimpleNamespace(
            text=json.dumps(payload))),
        close=lambda: None)
    client.app.state.rag.generator = generator
    response = client.post("/api/chat", json={"question": "What are the policies?"})
    assert response.status_code == 200
    assert response.json()["answer"] == "See both policies [S1] [S2]."
    assert len(response.json()["sources"]) == 2
    payload["answer"] = "See both policies."
    response = client.post("/api/chat", json={"question": "What are the policies?"})
    assert response.status_code == 200
    assert len(response.json()["sources"]) == 2
    payload["source_ids"] = ["S99"]
    assert client.post("/api/chat", json={"question": "What are the policies?"}).status_code == 502


@pytest.mark.parametrize("primary_status, fallback_status, expected_status, calls", [
    (200, 200, 200, 1),
    (503, 200, 200, 2),
    (504, 200, 200, 2),
    (None, 200, 200, 2),
    (429, 200, 200, 2),
    (403, 200, 502, 1),
    (503, 503, 503, 2),
])
def test_chat_model_fallback(client, primary_status, fallback_status, expected_status, calls):
    upload(client)
    requests = []

    def generate(**kwargs):
        requests.append(kwargs)
        status = primary_status if len(requests) == 1 else fallback_status
        if status is None:
            raise TimeoutException("Request expired")
        if status != 200:
            from google.genai.errors import APIError
            raise APIError(status, {"error": {"code": status, "message": "Service unavailable"}})
        return SimpleNamespace(text=json.dumps({"answer": "You may cancel [S1].", "source_ids": ["S1"]}))

    generator = GenerationService("test-key", "gemini-3.8-flash", "gemini-3.5-flash-lite")
    generator.client = SimpleNamespace(models=SimpleNamespace(generate_content=generate), close=lambda: None)
    client.app.state.rag.generator = generator
    response = client.post("/api/chat", json={"question": "Can I cancel?"})
    assert response.status_code == expected_status
    assert len(requests) == calls
    assert requests[0]["model"] == "gemini-3.8-flash"
    assert generator.model == "gemini-3.8-flash"
    if calls == 2:
        assert requests[1]["model"] == "gemini-3.5-flash-lite"
        assert requests[0]["contents"] == requests[1]["contents"]
    if expected_status == 200:
        assert response.json()["sources"][0]["source_id"] == "S1"
    elif calls == 2:
        assert "fallback also failed" in response.json()["detail"]


@pytest.mark.parametrize("provider_status", [200, 503])
def test_chat_through_gemini_sdk(client, monkeypatch, provider_status):
    upload(client)
    requests = []

    def respond(request):
        requests.append(request)
        payload = json.loads(request.content)
        context = json.loads(payload["contents"][0]["parts"][0]["text"])
        assert context["question"] == "Can I cancel?"
        assert context["passages"][0]["source_id"] == "S1"
        assert set(context["passages"][0]) == {"source_id", "text"}
        assert "tools" not in payload
        assert "temperature" not in payload["generationConfig"]
        assert payload["generationConfig"]["responseMimeType"] == "application/json"
        assert request.headers["x-server-timeout"] == "60"
        if provider_status == 503:
            return httpx.Response(503, json={"error": {
                "code": 503, "status": "UNAVAILABLE", "message": "Model is experiencing high demand"}})
        answer = json.dumps({"answer": "You may cancel [S1].", "source_ids": ["S1"]})
        return httpx.Response(200, json={"candidates": [{"content": {
            "role": "model", "parts": [{"text": answer}]}, "finishReason": "STOP"}]})

    create_client = genai.Client

    def mock_client(**kwargs):
        kwargs["http_options"].client_args = {"transport": httpx.MockTransport(respond)}
        return create_client(**kwargs)

    monkeypatch.setattr(genai, "Client", mock_client)
    client.app.state.rag.generator = GenerationService("test-key", "gemini-3.8-flash")
    response = client.post("/api/chat", json={"question": "Can I cancel?"})
    assert response.status_code == provider_status
    assert len(requests) == 1
    if provider_status == 200:
        assert response.json()["answer"] == "You may cancel [S1]."
        assert len(response.json()["sources"]) == 1
    else:
        assert "Gemini is busy" in response.json()["detail"]


@pytest.mark.parametrize("code, provider_message, status, reason, text", [
    (504, "", 504, "GATEWAY_TIMEOUT", "Gemini timed out"),
    (None, "", 504, "CLIENT_TIMEOUT", "60-second"),
    (503, "This model is currently experiencing high demand", 503, "MODEL_BUSY", "Gemini is busy"),
    (503, "Service unavailable", 503, "MODEL_UNAVAILABLE", "temporarily unavailable"),
    (429, "", 429, "RATE_LIMITED", "quota exceeded"),
    (404, "", 502, "MODEL_NOT_FOUND", "GEMINI_MODEL"),
    (403, "", 502, "ACCESS_DENIED", "project permissions"),
])
def test_chat_reports_gemini_errors(client, caplog, code, provider_message, status, reason, text):
    upload(client)
    class ProviderError(Exception):
        pass
    error = ProviderError()
    error.code, error.message = code, provider_message
    def fail(**kwargs):
        assert kwargs["config"].automatic_function_calling.disable is True
        raise TimeoutException("Request expired") if code is None else error
    generator = GenerationService("test-key", "test-model")
    generator.client = SimpleNamespace(models=SimpleNamespace(generate_content=fail), close=lambda: None)
    client.app.state.rag.generator = generator
    response = client.post("/api/chat", json={"question": "Can I cancel?"})
    assert response.status_code == status
    assert text in response.json()["detail"]
    assert "test-model" in response.json()["detail"]
    assert f"reason={reason}" in caplog.text

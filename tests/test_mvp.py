import io
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from qdrant_client import models

from app.main import create_app
from app.services.chunking import chunk_pages
from app.services.generation import GenerationError, GenerationService
from app.services.ingestion import RagService
from app.repositories.documents import DocumentRepository
from conftest import TestEmbeddings, TestGenerator, TestTokenizer, policy_pdf


def upload(client, name="policy.txt", text=b"Unopened products can be returned within 30 days of delivery."):
    return client.post("/api/documents", files={"file": (name, text)})


def test_end_to_end_payload_citations_original_and_deletion(client):
    result = upload(client)
    assert result.status_code == 201
    doc = result.json()["document"]
    assert doc["status"] == "ready" and doc["chunk_count"] == 1
    assert "storage_path" not in doc
    points, _ = client.app.state.rag.store.client.scroll(client.app.state.rag.store.collection, with_vectors=True)
    assert len(points[0].vector) == 1024
    assert points[0].payload["file_sha256"] == doc["file_sha256"]
    assert points[0].payload["text"].startswith("Unopened")
    answer = client.post("/api/chat", json={"question": "Can I return an unopened item?"})
    assert answer.status_code == 200
    source = answer.json()["sources"][0]
    assert source["source_id"] == "S1" and source["document_id"] == doc["document_id"]
    assert client.get(source["source_url"]).content.startswith(b"Unopened")
    assert client.delete(f"/api/documents/{doc['document_id']}").status_code == 204
    assert client.delete(f"/api/documents/{doc['document_id']}").status_code == 204
    assert client.get(doc["source_url"]).status_code == 404
    assert client.post("/api/retrieve", json={"question": "returns"}).json()["passages"] == []


def test_pdf_page_citation_and_original(client):
    pdf = policy_pdf(["Standard shipping takes five days.", "Unopened products may be returned within 30 days."])
    result = upload(client, "policy.pdf", pdf)
    assert result.status_code == 201, result.text
    passages = client.post("/api/retrieve", json={"question": "returns"}).json()["passages"]
    assert passages[0]["page_number"] == 2
    assert passages[0]["source_url"].endswith("#page=2")
    response = client.get(passages[0]["source_url"])
    assert response.content == pdf
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"].startswith("inline")


def test_duplicates_and_safe_filename(client):
    first = upload(client, "../../policy.txt").json()
    second = upload(client, "different-name.txt").json()
    assert first["document"]["filename"] == "policy.txt"
    assert second["duplicate"]
    assert first["document"]["document_id"] == second["document"]["document_id"]
    assert len(client.get("/api/documents").json()) == 1


@pytest.mark.parametrize("name,content,reason", [
    ("bad.docx", b"test", "Only"), ("empty.txt", b"", "empty"),
    ("encoding.txt", b"\xff\xfe", "UTF-8"), ("corrupt.pdf", b"not a PDF", "valid PDF"),
    ("spaces.txt", b" \n ", "no readable text"),
])
def test_rejected_documents(client, name, content, reason):
    response = upload(client, name, content)
    assert response.status_code == 422 and reason in response.json()["detail"]
    assert not client.post("/api/retrieve", json={"question": "anything"}).json()["passages"]


def test_scanned_encrypted_and_partially_scanned_pdf(client):
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    output = io.BytesIO()
    writer.write(output)
    assert "OCR" in upload(client, "scan.pdf", output.getvalue()).json()["detail"]
    writer.encrypt("password")
    output = io.BytesIO()
    writer.write(output)
    assert "Encrypted" in upload(client, "encrypted.pdf", output.getvalue()).json()["detail"]
    response = upload(client, "partial.pdf", policy_pdf(["Returns within 30 days.", ""]))
    assert response.status_code == 422 and "OCR" in response.json()["detail"]


def test_oversize_and_invalid_questions(client):
    assert upload(client, text=b"x" * (1024 * 1024 + 1)).status_code == 413
    for question in ["   ", "x" * 2001]:
        assert client.post("/api/chat", json={"question": question}).status_code == 422
    assert client.get("/api/documents/not-an-id/source").status_code == 422


def test_empty_database_does_not_generate(client):
    result = client.post("/api/chat", json={"question": "What is the policy?"})
    assert result.json()["status"] == "no_documents"
    assert client.app.state.rag.generator.calls == 0


def test_chunk_windows_preserve_pages_and_overlap():
    text = " ".join(f"word{i}" for i in range(100))
    chunks = chunk_pages([(1, text), (2, "A short useful paragraph.")], TestTokenizer(), 20, 5)
    assert all(0 < c.token_count <= 20 for c in chunks)
    assert chunks[0].text.split()[-5:] == chunks[1].text.split()[:5]
    assert chunks[-1].page_number == 2
    assert chunks[-1].text == "A short useful paragraph."
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_persistence_and_interrupted_ingestion_recovery(settings):
    rag = RagService(settings, TestEmbeddings(), TestGenerator())
    rag.load()
    doc = rag.ingest("policy.txt", b"Returns are accepted within 30 days.")["document"]
    rag.repo.update(doc["document_id"], "processing")
    rag.close()
    reopened = RagService(settings, TestEmbeddings(), TestGenerator())
    reopened.load()
    try:
        assert reopened.documents()[0]["status"] == "failed"
        assert reopened.retrieve("returns") == []
        reopened.delete(doc["document_id"])
        new_doc = reopened.ingest("policy.txt", b"Returns are accepted within 30 days.")["document"]
    finally:
        reopened.close()
    final = RagService(settings, TestEmbeddings(), TestGenerator())
    final.load()
    try:
        assert final.retrieve("returns")[0]["document_id"] == new_doc["document_id"]
    finally:
        final.close()


def test_partial_vector_write_is_rolled_back(client, monkeypatch):
    store = client.app.state.rag.store
    original = store.add
    def fail(points):
        original(points)
        raise RuntimeError("Simulated storage interruption")
    monkeypatch.setattr(store, "add", fail)
    assert upload(client).status_code == 422
    assert client.get("/api/documents").json()[0]["status"] == "failed"
    assert store.client.count(store.collection).count == 0


def test_registry_closes_connections_on_success_and_failure(tmp_path):
    path = tmp_path / "registry.sqlite3"
    repo = DocumentRepository(path)
    assert repo.all() == []
    with pytest.raises(RuntimeError):
        with repo.connect() as db:
            db.execute("SELECT 1")
            raise RuntimeError("abort")
    # Windows refuses this operation if a database connection remains open.
    moved = path.with_name("moved.sqlite3")
    path.rename(moved)
    moved.unlink()


def test_pages_and_health(client):
    for path in ["/", "/admin", "/static/styles.css", "/static/js/chat.js", "/docs", "/openapi.json"]:
        assert client.get(path).status_code == 200
    assert client.get("/api/health").json()["status"] == "ok"
    assert client.get("/api/ready").json()["ready"]


def test_missing_key_and_model_failure(settings):
    class BrokenEmbedding(TestEmbeddings):
        def load(self):
            raise RuntimeError("model unavailable")
    with TestClient(create_app(settings, BrokenEmbedding(), TestGenerator())) as client:
        client.app.state.rag.load()
        assert client.get("/api/ready").status_code == 503
        assert upload(client).status_code == 503
    with pytest.raises(GenerationError) as exc:
        GenerationService("", "test-model").generate("returns", [{"source_id": "S1"}])
    assert exc.value.status_code == 503


@pytest.mark.parametrize("payload", [
    '{"answer":"30 days [S9]", "source_ids":["S9"]}',
    '{"answer":"30 days [S1]", "source_ids":[]}',
    '{"answer":"30 days", "source_ids":["S1"]}', 'not JSON',
])
def test_invalid_provider_citations(payload):
    generator = GenerationService("test-key", "test-model")
    generator.client = SimpleNamespace(models=SimpleNamespace(generate_content=lambda **kwargs: SimpleNamespace(text=payload)))
    with pytest.raises(GenerationError):
        generator.generate("return window", [{"source_id": "S1", "filename": "policy.txt", "page_number": None, "text": "30 days"}])


def test_valid_generation_and_quota_error():
    passages = [{"source_id": "S1", "filename": "policy.txt", "page_number": None, "text": "30 days"}]
    generator = GenerationService("test-key", "test-model")
    generator.client = SimpleNamespace(models=SimpleNamespace(generate_content=lambda **kwargs: SimpleNamespace(
        text='{"answer":"30 days [S1]", "source_ids":["S1"]}')))
    assert generator.generate("returns", passages) == ("30 days [S1]", ["S1"])
    class QuotaError(Exception):
        code = 429
    def fail(**kwargs):
        raise QuotaError()
    generator.client.models.generate_content = fail
    with pytest.raises(GenerationError) as exc:
        generator.generate("returns", passages)
    assert exc.value.status_code == 429


def test_provider_overload_is_identified_without_exposing_credentials():
    class OverloadError(Exception):
        code = 503
    def fail(**kwargs):
        raise OverloadError("This model is currently experiencing high demand")
    generator = GenerationService("private-test-key", "test-model")
    generator.client = SimpleNamespace(models=SimpleNamespace(generate_content=fail))
    with pytest.raises(GenerationError) as exc:
        generator.generate("returns", [{"source_id": "S1", "filename": "policy.txt", "page_number": None, "text": "30 days"}])
    assert exc.value.status_code == 503
    assert "high demand" in str(exc.value)
    assert "private-test-key" not in str(exc.value)


@pytest.mark.parametrize("code", [500, 502, 503, 504])
def test_transient_provider_error_uses_fallback_with_same_citation_schema(code):
    class ProviderError(Exception):
        pass
    calls = []
    def generate(**kwargs):
        calls.append(kwargs)
        if kwargs["model"] == "primary":
            error = ProviderError()
            error.code = code
            raise error
        return SimpleNamespace(text='{"answer":"30 days [S1]", "source_ids":["S1"]}')
    service = GenerationService("secret", "primary", "fallback")
    service.client = SimpleNamespace(models=SimpleNamespace(generate_content=generate))
    answer, ids = service.generate("returns", [{"source_id": "S1", "filename": "policy.txt", "page_number": None, "text": "30 days"}])
    assert ids == ["S1"] and "30 days" in answer
    assert [call["model"] for call in calls] == ["primary", "fallback"]
    assert calls[0]["contents"] == calls[1]["contents"]
    assert calls[0]["config"].response_schema is calls[1]["config"].response_schema


@pytest.mark.parametrize("code", [400, 401, 403, 404, 429])
def test_quota_or_configuration_errors_do_not_switch_models(code):
    calls = []
    class ProviderError(Exception):
        pass
    def generate(**kwargs):
        calls.append(kwargs["model"])
        error = ProviderError()
        error.code = code
        raise error
    service = GenerationService("secret", "primary", "fallback")
    service.client = SimpleNamespace(models=SimpleNamespace(generate_content=generate))
    with pytest.raises(GenerationError):
        service.generate("returns", [{"source_id": "S1", "filename": "policy.txt", "page_number": None, "text": "30 days"}])
    assert calls == ["primary"]


def test_all_models_overloaded_and_duplicate_fallback_is_not_retried():
    class ProviderError(Exception):
        code = 503
    calls = []
    def fail(**kwargs):
        calls.append(kwargs["model"])
        raise ProviderError()
    for fallback, expected in [("primary", ["primary"]), ("fallback", ["primary", "fallback"])]:
        calls.clear()
        service = GenerationService("secret", "primary", fallback)
        service.client = SimpleNamespace(models=SimpleNamespace(generate_content=fail))
        with pytest.raises(GenerationError) as exc:
            service.generate("returns", [{"source_id": "S1", "filename": "policy.txt", "page_number": None, "text": "30 days"}])
        assert exc.value.status_code == 503
        assert calls == expected

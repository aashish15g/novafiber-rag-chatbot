import json
from types import SimpleNamespace
from uuid import uuid4

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

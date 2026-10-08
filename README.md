# NovaFiber customer service chatbot

A local RAG project using Python 3.14, FastAPI, vanilla JavaScript, Qdrant,
Qwen embeddings, and Gemini. No Docker is required.

## Setup

From the project folder in PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Copy the example only for a fresh setup; keep your existing `.env` if you already
have one. Set `GEMINI_API_KEY` and `GEMINI_MODEL` there. Never put the key in
JavaScript or commit it. Gemini uses one configured model with one request attempt;
there is no automatic model fallback.

Run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Use `--reload` during development. Run one worker because Qdrant is embedded.
Environment activation is optional when you use the full Python path above.

- Chat: http://127.0.0.1:8000/
- Document workspace: http://127.0.0.1:8000/admin
- API documentation: http://127.0.0.1:8000/docs

The first startup downloads the embedding model into `data/models`. Alternatively,
run `python scripts/check_embeddings.py` to download it first. Local embedding
inference has no per-request API charge. Gemini requires internet and an API key.

## Structure

```text
app/
  main.py                 App setup and lifecycle
  config.py               Environment settings
  schemas.py              Request and response models
  api/
    documents.py          Upload, list, delete, and sources
    chat.py               Retrieval and answers
    health.py             Health and readiness
    pages.py              Frontend pages
  services/
    extraction.py         PDF/TXT text extraction
    chunking.py           Overlapping token windows
    embeddings.py         Local Qwen model
    vector_store.py       Qdrant storage and search
    knowledge_registry.py NovaFiber article metadata
    generation.py         One Gemini request and citation validation
    rag.py                Connect the stages
  repositories/
    documents.py          SQLite document records
frontend/                 HTML, CSS, JavaScript
knowledge_base/           Fictional NovaFiber policies
scripts/                  Model download, corpus upload, PDF authoring
tests/                    Six basic request tests
```

Upload → extract pages → chunk → embed → store text, metadata, offsets, and vectors.
Question → embed → search → Gemini answer → clickable citations.
Sources open an extracted-text reader with the supporting passage highlighted,
plus a link to the original PDF page.

Qdrant stores passage vectors. SQLite tracks document records. Originals are saved
in `data/uploads`. Existing data is preserved; older generic demo documents are
excluded from NovaFiber search. New PDF/TXT uploads are NovaFiber policies by
default. Registered PDFs additionally receive article IDs, versions, and review
metadata. Known internal PDFs are rejected.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health`, `/api/ready` | Health and model readiness |
| GET/POST | `/api/documents` | List / upload documents |
| DELETE | `/api/documents/{id}` | Delete a document |
| GET | `/api/documents/{id}/source` | Original file |
| GET | `/api/documents/{id}/chunks/{chunk_id}` | Highlighted passage data |
| POST | `/api/retrieve` | Search passages |
| POST | `/api/chat` | Answer with citations |

Retrieval and chat accept `{"question": "How much is Everyday 300?"}`.
Uploads use multipart field `file`.

## Documents and tests

With the server ready, upload the 16 customer PDFs through the workspace or run:

```powershell
python scripts/ingest_knowledge_base.py
python -m pytest tests -q
```

Tests use temporary SQLite/Qdrant storage and small model substitutes. They check
routes, upload/retrieve/chat/delete, PDF metadata, basic invalid input, duplicates,
readiness, and the grouped-citation fix. They do not make live Gemini calls.

## Scope

This is a local learning MVP. Admin/customer pages have no login yet. PDF/TXT
extraction requires text; OCR and live account/outage data are not included.
One lock serializes local RAG operations; uploads can delay searches. Ingestion
failures mark the document failed with basic cleanup. There is no startup recovery
workflow, retry/backoff system, job queue, or automatic model switching.

Chunking uses 400-token windows and 60-token overlap. Existing indexed chunks are
unchanged; new uploads use the simpler splitter. Model or chunk-setting changes
require re-ingestion to update existing vectors. Stop the app before backing up
`data/uploads`, `data/app.sqlite3`, and `data/qdrant` together.

See [architecture](docs/architecture.md) for the request flow and design decisions.

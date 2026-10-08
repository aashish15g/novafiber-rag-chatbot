# NovaFiber customer service RAG chatbot

A customer-support chatbot for **NovaFiber**, a fictional residential broadband
company. It answers questions from uploaded policies and links users to the
supporting passages. I built it as a portfolio project to practice a complete
RAG pipeline and straightforward web application engineering.

See [the architecture guide](docs/architecture.md) for the request flow,
engineering decisions, and trade-offs.

## Implemented features

- Upload, list, and delete text-based PDF/TXT policies through an administrator workspace.
- Extract pages, create overlapping token chunks, and generate local embeddings.
- Persist vectors with chunk text, metadata, page numbers, and source offsets.
- Retrieve relevant passages and generate policy answers with Gemini.
- Open citations in a reader that highlights supporting text and links to the original PDF page.
- Use a retrieval inspector without a Gemini key.
- Attach article IDs, versions, and review metadata to the registered NovaFiber PDFs.

The repository includes **16 customer-facing policy PDFs** and four internal-only
examples. The customer corpus covers troubleshooting, equipment, billing/plans,
and FAQs. Known internal PDFs are rejected during upload.

## Technology stack

| Component | Technology |
|---|---|
| Backend | Python 3.14, FastAPI, Pydantic Settings |
| Frontend | HTML, CSS, vanilla JavaScript |
| Embeddings | `Qwen/Qwen3-Embedding-0.6B`, Sentence Transformers |
| Vector search | Embedded Qdrant, cosine similarity |
| Document records | SQLite |
| Answer generation | Gemini API; configurable model |
| PDF extraction | pypdf |
| Tests | pytest, FastAPI TestClient |

## Local setup

Use Python 3.14. These commands target Windows PowerShell:

```powershell
git clone https://github.com/aashish15g/novafiber-rag-chatbot.git
cd novafiber-rag-chatbot
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Copy the example only for a fresh setup; preserve an existing `.env`.
Set `GEMINI_API_KEY` to your own key. The sample model is
`gemini-3.1-flash-lite`; select a model available to your account.
Environment variables and `.env` override defaults in `app/config.py`.
Restart the server after changing them. Never commit a real key.

Run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Activation is optional because the command uses the virtual environment's Python.
You can add `--reload` during development. Use one worker: embedded Qdrant requires
a single server process.

- Customer chat: <http://127.0.0.1:8000/>
- Document workspace: <http://127.0.0.1:8000/admin>
- API docs: <http://127.0.0.1:8000/docs>

The first startup downloads Qwen into `data/models`, so it requires internet,
disk space, and sufficient RAM. The UI shows loading/readiness status.
To download the model separately:

```powershell
.\.venv\Scripts\python.exe scripts/check_embeddings.py
```

Embedding inference runs locally without an embedding API charge. Once the model
is fully cached, `$env:HF_HUB_OFFLINE = "1"` enables offline Hugging Face loading.
Gemini generation still requires internet and is subject to provider pricing,
quotas, and availability.

With the server ready, upload the customer PDFs or run:

```powershell
.\.venv\Scripts\python.exe scripts/ingest_knowledge_base.py
```

Original files, SQLite records, vectors, and model caches are created locally;
they are excluded from Git. A fresh clone needs to ingest the sample documents.

## How it works

**Documents:** upload → extract pages → chunk → embed → store.
Chunks use 400-token windows with 60-token overlap by default. Qdrant stores
normalized 1,024-dimensional vectors with evidence and metadata; SQLite tracks
document names, statuses, hashes, paths, and chunk counts.

**Questions:** embed question → search ready policies → send relevant passages
to Gemini → return the answer and cited sources. The source reader highlights
saved character ranges within extracted text; it does not annotate the PDF.

New uploads receive basic NovaFiber metadata. Registered PDF hashes identify
richer article metadata. Citation IDs must refer to retrieved sources; source
cards work even when Gemini omits inline labels. This verifies source identity,
not whether every generated claim is supported.

## Project structure

```text
app/
  main.py                App setup and lifecycle
  config.py              Settings and environment variables
  schemas.py             API request/response models
  api/                   Document, chat, health, and page routers
  services/              Extraction, chunking, embeddings, vector storage,
                         metadata lookup, generation, and RAG coordination
  repositories/          SQLite document records
frontend/                HTML, CSS, and JavaScript
knowledge_base/          Fictional policies, PDFs, registry, and sample questions
scripts/                 Corpus upload, model download, and PDF authoring
tests/                   Six basic request tests
docs/architecture.md     Flow diagram, decisions, and trade-offs
```

`requirements.in` lists direct app/test dependencies; `requirements.txt` pins
the environment used for development. Optional PDF authoring also needs ReportLab:

```powershell
.\.venv\Scripts\python.exe -m pip install reportlab
.\.venv\Scripts\python.exe scripts/build_knowledge_base.py
```

The existing PDFs are included, so this authoring step is not needed to run the app.

## API and tests

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health`, `/api/ready` | Health, model readiness, active Gemini model |
| GET/POST | `/api/documents` | List / upload documents |
| DELETE | `/api/documents/{id}` | Remove a document |
| GET | `/api/documents/{id}/source` | Original file |
| GET | `/api/documents/{id}/chunks/{chunk_id}` | Passage text and highlighting offsets |
| POST | `/api/retrieve` | Search passages |
| POST | `/api/chat` | Answer with citations |

Retrieval and chat accept `{"question": "How can I troubleshoot slow Wi-Fi?"}`.
Uploads use multipart field `file`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

Tests use real temporary SQLite/Qdrant storage and lightweight model substitutes.
They cover routes, upload/retrieve/chat/delete, PDF metadata, basic invalid input,
duplicate uploads, readiness, and citation cards. They do not call live Gemini or
measure real embedding quality. Sample retrieval questions are in
`knowledge_base/retrieval_questions.json`; they are evaluation data, not documents
to upload.

## Current limits and future work

This is a localhost learning MVP, not a production deployment. The administrator
and customer pages are separate workflows without login or enforced roles.
Extraction needs selectable text; OCR, conversation memory, live outages, and
customer account access are not implemented.

One lock serializes local RAG operations; uploads can delay searches. Basic cleanup
marks failed uploads, but there is no startup recovery, queue, retry/backoff system,
or model fallback. Changing chunk/model settings requires re-ingestion to update
existing vectors. Stop the app before backing up `data/uploads`,
`data/app.sqlite3`, and `data/qdrant` together.

Planned work includes authenticated roles, measured retrieval improvements, and
customer-authorized support ticket creation and tracking. These features are not
implemented yet.

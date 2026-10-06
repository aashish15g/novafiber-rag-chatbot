# Policy Desk — local customer service RAG MVP

Python **3.14**, FastAPI, vanilla JavaScript, persistent **embedded Qdrant**, local Qwen embeddings, and Gemini answer generation. No Docker or cloud database is required.

The administrator uploads policies. The assistant extracts and chunks them, stores the full text and metadata alongside embeddings, retrieves relevant passages, and generates answers with citations that open the original document. PDF citations include a page fragment for compatible browser viewers.

## Setup on Windows / PowerShell

```powershell
cd C:\Users\aashi\Desktop\CustomerRagBot
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip check
```

If PowerShell blocks environment activation, use `.\.venv\Scripts\python.exe` instead of `python`. No execution-policy change is necessary.

An ignored `.env` is provided with an empty Gemini key. For a fresh checkout, copy `.env.example` to `.env`. Get a Gemini key from [Google AI Studio](https://aistudio.google.com/apikey) and set:

```dotenv
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-3.8-flash
GEMINI_FALLBACK_MODEL=gemini-3.1-flash-lite
```

Never put the key in JavaScript or commit `.env`. The model ID is configurable because hosted model availability changes. The installed SDK uses `client.models.generate_content` with a structured response schema.

Temporary provider errors (HTTP 500/502/503/504) get at most two SDK attempts per model, with a short backoff and 20-second request timeout. If the primary remains unavailable, the optional `GEMINI_FALLBACK_MODEL` receives the same policy context and citation schema. Set the fallback to an empty value to disable it. Quota, authentication, permissions, invalid-model, and invalid-answer errors do not trigger model switching. Provider outages can still affect both models; fallback improves availability but cannot guarantee an answer. Server logs identify a fallback by model name and status, without logging the key or policy text.

To check a model without changing configuration, run `python scripts/check_gemini.py --model gemini-3.1-flash-lite --policy-check`. The diagnostic uses a synthetic policy, not your uploaded documents.

### Download and check the free embedding model

```powershell
.\.venv\Scripts\python.exe scripts/check_embeddings.py
```

This downloads `Qwen/Qwen3-Embedding-0.6B` into `data/models`, loads it on CPU, and checks actual semantic retrieval against synthetic return/shipping policies. The model weights are approximately 1.2 GB; allow extra disk space and RAM for the runtime. Local inference has no per-request model charge. The model uses an [Apache 2.0 license](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B).

The first model load can take time. The UI stays available while the model loads. The readiness banner updates automatically. If initialization fails, inspect the server log, resolve the issue, and restart. Model downloads require internet; cached embedding inference and Qdrant are local. Gemini answer generation always requires internet.

## Run

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Or run `./start.ps1`. For development, add `--reload`. Use **one worker**; embedded Qdrant storage must not be opened by multiple server processes.

- Customer chat: <http://127.0.0.1:8000/>
- Administrator/library: <http://127.0.0.1:8000/admin>
- API documentation: <http://127.0.0.1:8000/docs>

Upload `tests/fixtures/returns-policy.txt` and `tests/fixtures/shipping-policy.txt` from the library. They are synthetic, not real business policies. Try:

- Can I return an unopened product after two weeks?
- How many days does express shipping take?
- What is the refund processing time?

The administrator's **Retrieval inspector** works without a Gemini key. Chat answers require a key; the customer screen explains missing configuration rather than inventing an answer.

## Implemented flow

1. Validate a PDF/TXT upload, enforce the size limit, and identify duplicates using SHA-256.
2. Preserve the original under a generated UUID filename.
3. Extract PDF text page by page or decode UTF-8 TXT.
4. Split text using the model tokenizer (400 tokens, 60-token overlap), preferring sentence/paragraph boundaries and preserving source offsets.
5. Embed passages in batches of eight using normalized 1,024-dimensional vectors.
6. Store vectors with text, document ID, original filename, PDF page, chunk index, token count, UTC upload time, hash, embedding model, and chunking version.
7. Publish fully ingested documents; staging points are excluded from retrieval.
8. Embed the question with Qwen's query prompt and retrieve the top five ready passages using cosine similarity.
9. Generate a grounded Gemini answer; validate declared and inline citation IDs against the retrieved sources.
10. Return only cited passages and links to the preserved original files.

Similarity scores rank passages; they are not answer confidence. Citation-ID validation cannot independently prove that a claim is supported, so answers still need policy-specific evaluation.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Process health |
| GET | `/api/ready` | Embedding readiness and generation configuration |
| POST | `/api/documents` | Multipart upload; field name `file` |
| GET | `/api/documents` | Registry records without internal storage paths |
| DELETE | `/api/documents/{document_id}` | Idempotent removal of vectors, original, and registry record |
| GET | `/api/documents/{document_id}/source` | Serve an indexed original inline |
| POST | `/api/retrieve` | Retrieved passages with scores and source links |
| POST | `/api/chat` | Grounded answer and citations |

Retrieval/chat input:

```json
{"question": "What is the return window?"}
```

Example answer:

```json
{
  "answer": "Unopened items may be returned within 30 days. [S1]",
  "status": "answered",
  "sources": [{
    "source_id": "S1",
    "document_id": "document-uuid",
    "filename": "returns-policy.pdf",
    "page_number": 2,
    "chunk_index": 0,
    "excerpt": "Unopened items may be returned within 30 days...",
    "source_url": "/api/documents/document-uuid/source#page=2"
  }]
}
```

TXT sources use passage numbers instead of PDF pages. Citations open in a new browser tab. Source access is local and unauthenticated in this MVP; authorization will be enforced when JWT is added.

## Configuration

See `.env.example`. Relative storage paths resolve against the project root.

- `CHUNK_SIZE_TOKENS=400`, `CHUNK_OVERLAP_TOKENS=60`
- `RETRIEVAL_TOP_K=5`, `MAX_UPLOAD_MB=10`
- `EMBEDDING_DEVICE=cpu`
- `QDRANT_PATH=./data/qdrant`
- `QDRANT_COLLECTION=customer_policies_qwen3_1024_v1`

Changing a model, tokenizer, or chunking settings does not update already indexed data. Re-ingest originals into a new collection/database before switching. Collection startup rejects incompatible vector dimensions or distance configuration.

## Failure handling and persistence

SQLite records and Qdrant do not share a transaction. Ingestion is serialized; points remain `indexing` until completion. Failure deletes partial vectors and marks the document failed. Startup removes vectors from interrupted processing records. Interrupted deletions are completed on restart. Failed originals remain available on disk for diagnosis; delete the failed record and reupload to retry.

The backend never trusts client filenames as paths. Source routes resolve UUIDs through the registry and keep file paths within the uploads directory. Original PDFs are served as PDFs; TXT is served as plain text. Frontend output uses text nodes, not raw HTML.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
node --check frontend/js/common.js
node --check frontend/js/admin.js
node --check frontend/js/chat.js
```

Automated tests use **real embedded Qdrant and SQLite** with isolated temporary data, deterministic test embeddings, and mocked generation. They cover PDF pages, metadata, citation links, duplicate files, invalid formats/encoding, encrypted/scanned PDFs, size limits, rollback, interruption recovery, restart persistence, deletion, missing configuration, and provider citation/quota failures.

The separate embedding smoke script checks the real model. Live Gemini answers cannot be validated until a valid API key is configured. Two upstream Python/SDK deprecation warnings may appear in tests; they do not indicate failed application checks.

## Backup, restore, and reset

Stop the server cleanly before copying `data/uploads`, `data/app.sqlite3`, and `data/qdrant` together. Keep matching document and vector data. Restore that complete set while the application is stopped, then restart and inspect the document list and a known retrieval. `data/models` is a replaceable download cache.

For a reversible reset, stop the server and rename `data` to a dated backup folder. On restart the app creates an empty workspace and may redownload the model. To keep the cache, retain `data/models` and move the other three paths to a backup folder instead. Do not reset while the application is running.

## MVP boundaries and next milestones

This is a localhost learning MVP with separate workflows, **not enforced admin/customer roles**. Keep it bound to `127.0.0.1`. Use public/synthetic policies with Gemini's free tier, whose [pricing page](https://ai.google.dev/gemini-api/docs/pricing) documents quotas and content-use terms.

Current boundaries: PDF/TXT only; all PDF pages must have extractable text; no OCR, DOCX, conversation memory, hybrid retrieval, reranker, queue, JWT, or deployment infrastructure. PDF tables and complex layouts require later extraction improvements. Upload processing is synchronous from the browser's perspective; heavy work runs off the event loop. The app serializes local vector access for reliability rather than parallel ingestion.

After MVP acceptance:

1. Establish a 30–50-question retrieval/grounding evaluation set.
2. Improve chunking, metadata filtering, hybrid retrieval, reranking, and adjacent context one change at a time.
3. Add JWT, Argon2 password hashes, and backend permissions, including original-source access.
4. Add policy versions, effective dates, DOCX, OCR, durable ingestion jobs, and follow-up query rewriting.
5. Choose hosting and migrate to server Qdrant only when deployment becomes the objective.

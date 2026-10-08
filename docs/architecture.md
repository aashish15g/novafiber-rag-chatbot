# Architecture

The application has three straightforward layers:

1. **Routes** handle HTTP input and responses.
2. **RagService** connects the document and question workflows.
3. **Small modules** perform extraction, chunking, embedding, storage, and generation.

## Follow the code

`main.py` creates the services and registers the routers. It loads Qwen in a
background thread so the frontend can show a loading state. Configuration comes
from `.env` through `config.py`.

`api/documents.py` reads an upload asynchronously, checks its size, and runs
blocking ingestion in a thread pool. The service saves the original, extracts
pages, creates overlapping token windows, embeds them, and stores Qdrant points.
SQLite records the document's name, status, and metadata.

`api/chat.py` calls retrieval and generation. Qwen embeds the question; Qdrant
returns passages; Gemini receives those passages and returns an answer with
source IDs. The service returns the cited passages to the browser.

`api/documents.py` also serves originals and passage details. The source reader
uses page character offsets to highlight evidence. A small text-match check
prevents showing an unrelated highlight.

## Why these choices

- Qdrant handles vector search; SQLite handles document records.
- Metadata lives beside each vector so retrieval returns evidence and provenance.
- One local lock coordinates ingestion, retrieval, and deletion.
- Blocking model/database calls remain in synchronous FastAPI routes, which run
  in a thread pool. Async is used for upload reads and application lifecycle.
- Gemini uses one model and one attempt. Citation validation remains because
  invented or mismatched sources would break a core feature.
- Frontend helpers share API calls, source cards, and the NovaFiber shell.

The six tests check basic request behavior with isolated storage and model
substitutes. They avoid live network calls and failure-injection machinery.

This is a single-process local MVP. It has no authenticated roles, queues,
automatic model fallback, backoff logic, or startup reconciliation. Explain
these boundaries before describing future features in an interview.

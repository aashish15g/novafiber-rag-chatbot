from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/ready")
def ready(request: Request):
    rag = request.app.state.rag
    return JSONResponse(status_code=200 if rag.ready else 503, content={
        "ready": rag.ready,
        "embeddings": "ready" if rag.ready else "failed" if rag.startup_error else "loading",
        "generation_configured": bool(rag.generator.api_key),
        "embedding_model": rag.settings.embedding_model,
        "gemini_model": rag.settings.gemini_model,
        "max_upload_mb": rag.settings.max_upload_mb,
        "detail": rag.startup_error or ("Ready" if rag.ready else "Loading the embedding model…")
    })

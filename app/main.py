import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import chat, documents
from app.config import ROOT, Settings
from app.services.embeddings import EmbeddingService
from app.services.generation import GenerationError, GenerationService
from app.services.ingestion import RagService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def create_app(settings=None, embeddings=None, generator=None):
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app):
        rag = RagService(settings, embeddings or EmbeddingService(settings.embedding_model, settings.embedding_device, settings.data_dir / "models"),
                         generator or GenerationService(settings.gemini_api_key, settings.gemini_model, settings.gemini_fallback_model))
        app.state.rag = rag
        # Show the UI while a first-time model download/load runs.
        loader = threading.Thread(target=rag.load, name="embedding-loader", daemon=True)
        loader.start()
        try:
            yield
        finally:
            loader.join()
            rag.close()

    app = FastAPI(title="Policy Desk", version="0.1.0", lifespan=lifespan)
    app.include_router(documents.router)
    app.include_router(chat.router)
    app.mount("/static", StaticFiles(directory=ROOT / "frontend"), name="static")

    @app.exception_handler(GenerationError)
    async def generation_error(request: Request, exc: GenerationError):
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

    @app.get("/api/health", tags=["Health"])
    def health():
        return {"status": "ok", "version": "0.1.0"}

    @app.get("/api/ready", tags=["Health"])
    def ready(request: Request):
        rag = request.app.state.rag
        return JSONResponse(status_code=200 if rag.ready else 503, content={
            "ready": rag.ready, "embeddings": "ready" if rag.ready else "failed" if rag.startup_error else "loading",
            "generation_configured": bool(settings.gemini_api_key) or generator is not None,
            "embedding_model": settings.embedding_model, "gemini_model": settings.gemini_model,
            "gemini_fallback_model": settings.gemini_fallback_model,
            "max_upload_mb": settings.max_upload_mb,
            "detail": rag.startup_error or ("Ready" if rag.ready else "Loading the local embedding model…"),
        })

    @app.get("/", include_in_schema=False)
    def customer():
        return FileResponse(ROOT / "frontend" / "index.html")

    @app.get("/admin", include_in_schema=False)
    def admin():
        return FileResponse(ROOT / "frontend" / "admin.html")

    return app


app = create_app()

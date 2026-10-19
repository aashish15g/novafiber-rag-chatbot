import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import auth, chat, documents, health, pages
from app.config import ROOT, Settings
from app.services.embeddings import EmbeddingService
from app.services.generation import GenerationError, GenerationService
from app.services.rag import RagService
from app.repositories.users import UserRepository

logging.basicConfig(level=logging.INFO)


def create_app(settings=None, embeddings=None, generator=None):
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app):
        if len(settings.jwt_secret) < 32:
            raise RuntimeError("Set JWT_SECRET in .env to a random value of at least 32 characters.")
        app.state.settings = settings
        app.state.users = UserRepository(settings.data_dir / "app.sqlite3")
        rag = RagService(
            settings,
            embeddings or EmbeddingService(settings.embedding_model, settings.embedding_device, settings.data_dir / "models"),
            generator or GenerationService(settings.gemini_api_key, settings.gemini_model,
                                           settings.gemini_fallback_model))
        app.state.rag = rag
        # Load in the background so the UI can show its loading state.
        loader = threading.Thread(target=rag.load, daemon=True)
        loader.start()
        try:
            yield
        finally:
            loader.join()
            rag.close()

    app = FastAPI(title="NovaFiber Support", lifespan=lifespan)
    for router in [auth.router, documents.router, chat.router, health.router, pages.router]:
        app.include_router(router)
    app.mount("/static", StaticFiles(directory=ROOT / "frontend"), name="static")

    @app.exception_handler(GenerationError)
    async def generation_error(request: Request, exc: GenerationError):
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

    return app


app = create_app()

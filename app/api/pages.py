from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.config import ROOT

router = APIRouter(include_in_schema=False)


@router.get("/")
def customer():
    return FileResponse(ROOT / "frontend/index.html")


@router.get("/admin")
def admin():
    return FileResponse(ROOT / "frontend/admin.html")


@router.get("/sources/{document_id}/{chunk_id}")
def source_reader(document_id: UUID, chunk_id: UUID):
    return FileResponse(ROOT / "frontend/source.html")

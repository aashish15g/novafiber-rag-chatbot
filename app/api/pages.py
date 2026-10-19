from uuid import UUID
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse

from app.api.dependencies import get_current_user, require_admin
from app.config import ROOT

router = APIRouter(include_in_schema=False)


def protected_page(request, filename, admin=False):
    try:
        user = get_current_user(request)
        if admin:
            require_admin(user)
    except HTTPException as error:
        if error.status_code == 401:
            return RedirectResponse("/login?next=" + quote(request.url.path, safe="/"), status_code=303)
        raise
    return FileResponse(ROOT / "frontend" / filename, headers={"Cache-Control": "no-store"})


@router.get("/login")
def login_page():
    return FileResponse(ROOT / "frontend/login.html", headers={"Cache-Control": "no-store"})


@router.get("/")
def customer(request: Request):
    return protected_page(request, "index.html")


@router.get("/admin")
def admin(request: Request):
    return protected_page(request, "admin.html", admin=True)


@router.get("/sources/{document_id}/{chunk_id}")
def source_reader(document_id: UUID, chunk_id: UUID, request: Request):
    return protected_page(request, "source.html")

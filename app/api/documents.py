from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response
from starlette.concurrency import run_in_threadpool

from app.schemas import Document, UploadResponse
from app.services.extraction import DocumentError
from app.api.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.get("", response_model=list[Document], dependencies=[Depends(require_admin)])
def documents(request: Request):
    return request.app.state.rag.documents()


@router.post("", response_model=UploadResponse, status_code=201, dependencies=[Depends(require_admin)])
async def upload(request: Request, file: UploadFile = File(...)):
    service = request.app.state.rag
    service.require_ready()
    try:
        limit = service.settings.max_upload_mb * 1024 * 1024
        data = await file.read(limit + 1)
        if len(data) > limit:
            raise HTTPException(413, f"Maximum upload size is {service.settings.max_upload_mb} MB.")
        return await run_in_threadpool(service.ingest, file.filename or "document", data)
    except DocumentError as exc:
        raise HTTPException(422, str(exc)) from exc
    finally:
        await file.close()


@router.delete("/{document_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete(document_id: UUID, request: Request):
    request.app.state.rag.delete(str(document_id))
    return Response(status_code=204)


@router.get("/{document_id}/source", dependencies=[Depends(get_current_user)])
def source(document_id: UUID, request: Request):
    result = request.app.state.rag.source(str(document_id))
    if result is None:
        raise HTTPException(404, "Source document is unavailable.")
    record, path = result
    media = "application/pdf" if path.suffix == ".pdf" else "text/plain; charset=utf-8"
    return FileResponse(path, filename=record["filename"], media_type=media,
                        content_disposition_type="inline", headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store"})


@router.get("/{document_id}/chunks/{chunk_id}", dependencies=[Depends(get_current_user)])
def passage(document_id: UUID, chunk_id: UUID, request: Request):
    try:
        result = request.app.state.rag.passage(str(document_id), str(chunk_id))
    except DocumentError as exc:
        raise HTTPException(409, str(exc)) from exc
    if result is None:
        raise HTTPException(404, "Source passage is unavailable.")
    return result

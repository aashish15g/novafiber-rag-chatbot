from uuid import UUID

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response
from starlette.concurrency import run_in_threadpool

from app.schemas import Document, UploadResponse
from app.services.extraction import DocumentError

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.get("", response_model=list[Document])
def documents(request: Request):
    return request.app.state.rag.documents()


@router.post("", response_model=UploadResponse, status_code=201)
async def upload(request: Request, file: UploadFile = File(...)):
    service = request.app.state.rag
    service.require_ready()
    data = bytearray()
    try:
        while block := await file.read(1024 * 1024):
            data.extend(block)
            if len(data) > service.settings.max_upload_mb * 1024 * 1024:
                raise HTTPException(413, f"Maximum upload size is {service.settings.max_upload_mb} MB.")
        return await run_in_threadpool(service.ingest, file.filename or "document", bytes(data))
    except DocumentError as exc:
        raise HTTPException(422, str(exc)) from exc
    finally:
        await file.close()


@router.delete("/{document_id}", status_code=204)
def delete(document_id: UUID, request: Request):
    request.app.state.rag.delete(str(document_id))
    return Response(status_code=204)


@router.get("/{document_id}/source")
def source(document_id: UUID, request: Request):
    result = request.app.state.rag.source(str(document_id))
    if result is None:
        raise HTTPException(404, "Source document is unavailable.")
    record, path = result
    media = "application/pdf" if path.suffix == ".pdf" else "text/plain; charset=utf-8"
    return FileResponse(path, filename=record["filename"], media_type=media,
                        content_disposition_type="inline", headers={"X-Content-Type-Options": "nosniff"})

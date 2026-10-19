from fastapi import APIRouter, Depends, Request

from app.schemas import ChatResponse, QuestionRequest, RetrievalResponse
from app.api.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/retrieve", response_model=RetrievalResponse, dependencies=[Depends(require_admin)])
def retrieve(body: QuestionRequest, request: Request):
    return {"passages": request.app.state.rag.retrieve(body.question)}


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(get_current_user)])
def chat(body: QuestionRequest, request: Request):
    return request.app.state.rag.chat(body.question)

from fastapi import APIRouter, Request

from app.schemas import ChatResponse, QuestionRequest, RetrievalResponse

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/retrieve", response_model=RetrievalResponse)
def retrieve(body: QuestionRequest, request: Request):
    return {"passages": request.app.state.rag.retrieve(body.question)}


@router.post("/chat", response_model=ChatResponse)
def chat(body: QuestionRequest, request: Request):
    return request.app.state.rag.chat(body.question)

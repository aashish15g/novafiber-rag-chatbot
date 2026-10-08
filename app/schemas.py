from pydantic import BaseModel, Field, field_validator
from typing import Any


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def clean_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Enter a question.")
        return value


class Source(BaseModel):
    source_id: str
    document_id: str
    filename: str
    page_number: int | None
    chunk_index: int
    excerpt: str
    source_url: str
    passage_url: str | None = None
    chunk_id: str | None = None
    char_start: int | None = None
    char_end: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Passage(Source):
    text: str
    score: float


class RetrievalResponse(BaseModel):
    passages: list[Passage]


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    status: str = "answered"


class Document(BaseModel):
    document_id: str
    filename: str
    file_sha256: str
    uploaded_at: str
    status: str
    chunk_count: int
    error: str | None
    source_url: str
    searchable: bool
    metadata: dict[str, Any] = Field(default_factory=dict)


class UploadResponse(BaseModel):
    document: Document
    duplicate: bool

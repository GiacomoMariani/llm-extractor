from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    chunk_count: int


class DocumentIngestionJobResponse(BaseModel):
    job_id: str
    filename: str
    status: str
    document_id: str | None = None
    chunk_count: int | None = None
    error_message: str | None = None
    created_at: str
    updated_at: str


class DocumentAskRequest(BaseModel):
    document_id: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=10)


class Citation(BaseModel):
    chunk_id: str
    snippet: str
    vector_score: float
    keyword_score: float
    hybrid_score: float


class DocumentAskResponse(BaseModel):
    answer: str
    citations: list[Citation]
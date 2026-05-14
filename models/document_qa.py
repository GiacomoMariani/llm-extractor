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
    filename: str
    page_number: int | None = None
    snippet: str
    vector_score: float
    keyword_score: float
    hybrid_score: float


class DocumentSummaryResponse(BaseModel):
    document_id: str
    filename: str
    chunk_count: int


class DocumentListResponse(BaseModel):
    documents: list[DocumentSummaryResponse]


class DocumentDeleteResponse(BaseModel):
    document_id: str
    deleted: bool


class DocumentAskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    was_fallback: bool = False


class DocumentReindexResponse(BaseModel):
    job_id: str
    document_id: str
    filename: str
    status: str


class DocumentQueryRetrievedSourceLogResponse(BaseModel):
    source_id: str
    query_id: str
    chunk_id: str
    filename: str
    snippet: str
    page_number: int | None = None
    vector_score: float
    keyword_score: float
    hybrid_score: float


class DocumentQueryLogResponse(BaseModel):
    query_id: str
    document_id: str
    question: str
    answer: str
    citation_count: int
    latency_ms: float
    was_fallback: bool
    created_at: str
    retrieved_sources: list[DocumentQueryRetrievedSourceLogResponse] = Field(
        default_factory=list
    )


class DocumentQueryLogListResponse(BaseModel):
    logs: list[DocumentQueryLogResponse]


class KnowledgeGapResponse(BaseModel):
    query_id: str
    document_id: str
    question: str
    answer: str
    citation_count: int
    latency_ms: float
    created_at: str


class KnowledgeGapListResponse(BaseModel):
    gaps: list[KnowledgeGapResponse]
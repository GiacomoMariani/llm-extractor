from pydantic import BaseModel, Field


class DocumentQAEvalCase(BaseModel):
    name: str
    document_filename: str = "eval_document.txt"
    document_text: str = Field(min_length=1)
    question: str = Field(min_length=1)
    expected_answer_contains: list[str] = Field(default_factory=list)
    expected_citation_contains: list[str] = Field(default_factory=list)
    min_citations: int = Field(default=1, ge=0)
    require_retrieval_scores: bool = True


class DocumentQAEvalCaseResult(BaseModel):
    name: str
    passed: bool
    answer: str
    citation_count: int
    checks: list[str]
    failures: list[str]
    latency_ms: float
    document_id: str | None = None


class DocumentQAEvalSummary(BaseModel):
    total_cases: int
    passed: int
    failed: int
    average_latency_ms: float
    results: list[DocumentQAEvalCaseResult]


class DocumentQAEvalStoredCaseResultResponse(BaseModel):
    name: str
    passed: bool
    answer: str
    citation_count: int
    checks: list[str]
    failures: list[str]
    latency_ms: float
    document_id: str | None = None


class DocumentQAEvalLatestRunResponse(BaseModel):
    run_id: str
    total_cases: int
    passed: int
    failed: int
    average_latency_ms: float
    created_at: str
    results: list[DocumentQAEvalStoredCaseResultResponse]
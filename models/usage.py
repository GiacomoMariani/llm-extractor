from pydantic import BaseModel, Field


class UsageRecordResponse(BaseModel):
    usage_id: str
    operation: str
    provider: str
    model_name: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    metadata: dict[str, str]
    created_at: str


class UsageSummaryResponse(BaseModel):
    total_estimated_cost_usd: float
    recent_record_count: int


class UsageRecentResponse(BaseModel):
    records: list[UsageRecordResponse]


class UsageRecentRequest(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
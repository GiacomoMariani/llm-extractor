from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    max_sentences: int = Field(default=2, ge=1, le=5)


class SummarizeResponse(BaseModel):
    summary: str
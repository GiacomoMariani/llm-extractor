from pydantic import BaseModel, Field


class ExtractRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class ExtractResponse(BaseModel):
    email: str | None
    order_id: str | None
    urgency: str
    has_refund_request: bool
from pydantic import BaseModel, Field


class UploadedTextCleanupRequest(BaseModel):
    max_age_hours: int | None = Field(default=None, gt=0, le=24 * 30)


class UploadedTextCleanupResponse(BaseModel):
    deleted_count: int
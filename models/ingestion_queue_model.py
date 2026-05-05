from pydantic import BaseModel, Field


class TextUploadIngestionPayload(BaseModel):
    job_id: str = Field(..., min_length=1)
    filename: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)


class StoredTextUploadIngestionPayload(BaseModel):
    job_id: str = Field(..., min_length=1)
    filename: str = Field(..., min_length=1)
    content_id: str = Field(..., min_length=1)
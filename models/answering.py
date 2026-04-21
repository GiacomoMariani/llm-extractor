from pydantic import BaseModel, Field


class AnswerRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    context: str = Field(min_length=1, max_length=10000)


class AnswerResponse(BaseModel):
    answer: str
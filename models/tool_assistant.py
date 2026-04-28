from typing import Any

from pydantic import BaseModel, Field


class ToolAssistantRequest(BaseModel):
    message: str


class ToolCallRecord(BaseModel):
    tool_name: str
    result: dict[str, Any]


class ToolAssistantResponse(BaseModel):
    answer: str

    # Backward-compatible single-tool fields.
    # These are useful for simple cases and keep existing tests stable.
    tool_called: str | None = None
    tool_result: dict[str, Any] | None = None

    # New multi-step field.
    # This records the full sequence of tool calls.
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
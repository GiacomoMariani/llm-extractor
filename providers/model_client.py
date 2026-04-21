from typing import Protocol


class ModelClient(Protocol):
    async def complete(self, prompt: str) -> str:
        ...
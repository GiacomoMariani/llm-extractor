from openai import AsyncOpenAI

from providers.model_client import ModelClient


class OpenAIDocumentQAModelClient(ModelClient):
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.client = AsyncOpenAI()

    async def complete(self, prompt: str) -> str:
        response = await self.client.responses.create(
            model=self.model_name,
            input=prompt,
        )

        return response.output_text.strip()
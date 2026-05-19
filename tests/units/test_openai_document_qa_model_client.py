from types import SimpleNamespace

import pytest

from providers.openai_document_qa_model_client import (
    OpenAIDocumentQAModelClient,
)


class StubResponses:
    def __init__(self):
        self.calls = []

    async def create(self, model: str, input: str):
        self.calls.append(
            {
                "model": model,
                "input": input,
            }
        )

        return SimpleNamespace(output_text=" Grounded answer. [1] ")


class StubAsyncOpenAI:
    def __init__(self):
        self.responses = StubResponses()


@pytest.mark.asyncio
async def test_openai_document_qa_model_client_completes_prompt(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    client = OpenAIDocumentQAModelClient(
        model_name="gpt-4.1-mini",
    )
    stub_client = StubAsyncOpenAI()
    client.client = stub_client

    result = await client.complete("Answer from this context only.")

    assert result == "Grounded answer. [1]"
    assert stub_client.responses.calls == [
        {
            "model": "gpt-4.1-mini",
            "input": "Answer from this context only.",
        }
    ]
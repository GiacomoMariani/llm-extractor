import os

from providers.fake_document_qa_model_client import FakeDocumentQAModelClient
from providers.model_client import ModelClient
from providers.openai_document_qa_model_client import OpenAIDocumentQAModelClient
from settings import Settings


def get_document_qa_model_client(settings: Settings) -> ModelClient:
    if settings.document_qa_model_client_type == "fake":
        return FakeDocumentQAModelClient()

    if settings.document_qa_model_client_type == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError(
                "OPENAI_API_KEY is required when "
                "DOCUMENT_QA_MODEL_CLIENT_TYPE=openai."
            )

        return OpenAIDocumentQAModelClient(
            model_name=settings.document_qa_model_name,
        )

    raise ValueError(
        "Unsupported DOCUMENT_QA_MODEL_CLIENT_TYPE. "
        "Supported values: fake, openai."
    )
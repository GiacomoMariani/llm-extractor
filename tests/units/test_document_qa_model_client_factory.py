import pytest

from providers.document_qa_model_client_factory import (
    get_document_qa_model_client,
)
from providers.fake_document_qa_model_client import FakeDocumentQAModelClient
from providers.openai_document_qa_model_client import OpenAIDocumentQAModelClient
from settings import Settings


def test_get_document_qa_model_client_returns_fake_client():
    client = get_document_qa_model_client(
        Settings(document_qa_model_client_type="fake")
    )

    assert isinstance(client, FakeDocumentQAModelClient)


def test_get_document_qa_model_client_returns_openai_client():
    client = get_document_qa_model_client(
        Settings(
            document_qa_model_client_type="openai",
            document_qa_model_name="gpt-4.1-mini",
        )
    )

    assert isinstance(client, OpenAIDocumentQAModelClient)
    assert client.model_name == "gpt-4.1-mini"


def test_get_document_qa_model_client_rejects_unsupported_client_type():
    with pytest.raises(ValueError) as exc_info:
        get_document_qa_model_client(
            Settings(document_qa_model_client_type="unsupported")
        )

    message = str(exc_info.value)

    assert "Unsupported DOCUMENT_QA_MODEL_CLIENT_TYPE" in message
    assert "fake" in message
    assert "openai" in message
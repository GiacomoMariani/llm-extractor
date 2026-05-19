import pytest

from providers.fake_document_qa_model_client import FakeDocumentQAModelClient


@pytest.mark.asyncio
async def test_fake_document_qa_model_client_answers_from_first_context_line():
    client = FakeDocumentQAModelClient()

    response = await client.complete(
        """Question:
What is the refund policy?

Retrieved context:
[1] policy.pdf, page 4
Refunds are available within 30 days.

Answer:
"""
    )

    assert response == "Refunds are available within 30 days. [1]"


@pytest.mark.asyncio
async def test_fake_document_qa_model_client_falls_back_without_context():
    client = FakeDocumentQAModelClient()

    response = await client.complete(
        """Question:
What is the refund policy?

Retrieved context:

Answer:
"""
    )

    assert response == (
        "I could not find this information in the uploaded documents."
    )
    
def test_fake_document_qa_model_client_has_model_name():
    client = FakeDocumentQAModelClient()

    assert client.model_name == "fake-document-qa"
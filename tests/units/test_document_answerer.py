import pytest

from services.document_answerer import RuleBasedDocumentAnswerer
from services.document_qa_prompt_builder import RetrievedContextBlock
from services.rule_based_answerer import RuleBasedAnswerer


@pytest.mark.asyncio
async def test_rule_based_document_answerer_combines_context_blocks():
    answerer = RuleBasedDocumentAnswerer(
        answerer=RuleBasedAnswerer(),
    )

    result = await answerer.answer(
        question="What backend framework is used?",
        context_blocks=[
            RetrievedContextBlock(
                source_id=1,
                filename="guide.txt",
                page_number=None,
                text="The frontend uses Streamlit.",
            ),
            RetrievedContextBlock(
                source_id=2,
                filename="guide.txt",
                page_number=None,
                text="FastAPI is the backend framework used in this project.",
            ),
        ],
    )

    assert result.was_fallback is False
    assert result.answer == "FastAPI is the backend framework used in this project."
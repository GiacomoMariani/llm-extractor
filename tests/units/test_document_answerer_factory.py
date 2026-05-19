import pytest

from services.document_answerer import (
    FallbackDocumentAnswerer,
    RuleBasedDocumentAnswerer,
)
from services.document_answerer_factory import get_document_answerer
from services.llm_document_answerer import LLMDocumentAnswerer
from settings import Settings


def test_get_document_answerer_returns_rule_based_answerer_by_default():
    answerer = get_document_answerer(
        Settings(document_answerer_type="rule")
    )

    assert isinstance(answerer, RuleBasedDocumentAnswerer)


def test_get_document_answerer_returns_llm_answerer_with_rule_fallback_by_default():
    answerer = get_document_answerer(
        Settings(document_answerer_type="llm")
    )

    assert isinstance(answerer, FallbackDocumentAnswerer)
    assert answerer.model_name == "fake-document-qa+fallback-rule"


def test_get_document_answerer_returns_llm_answerer_without_rule_fallback():
    answerer = get_document_answerer(
        Settings(
            document_answerer_type="llm",
            document_qa_fallback_to_rule=False,
        )
    )

    assert isinstance(answerer, LLMDocumentAnswerer)
    assert answerer.model_name == "fake-document-qa"


def test_get_document_answerer_rejects_unsupported_answerer_type():
    with pytest.raises(ValueError) as exc_info:
        get_document_answerer(
            Settings(document_answerer_type="unsupported")
        )

    message = str(exc_info.value)

    assert "Unsupported DOCUMENT_ANSWERER_TYPE" in message
    assert "rule" in message
    assert "llm" in message
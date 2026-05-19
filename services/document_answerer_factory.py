from providers.document_qa_model_client_factory import (
    get_document_qa_model_client,
)
from services.document_answerer import (
    DocumentAnswerer,
    FallbackDocumentAnswerer,
    RuleBasedDocumentAnswerer,
)
from services.llm_document_answerer import LLMDocumentAnswerer
from services.rule_based_answerer import RuleBasedAnswerer
from settings import Settings


def get_document_answerer(settings: Settings) -> DocumentAnswerer:
    rule_answerer = RuleBasedDocumentAnswerer(
        answerer=RuleBasedAnswerer(),
    )

    if settings.document_answerer_type == "rule":
        return rule_answerer

    if settings.document_answerer_type == "llm":
        llm_answerer = LLMDocumentAnswerer(
            model_client=get_document_qa_model_client(settings),
        )

        if settings.document_qa_fallback_to_rule:
            return FallbackDocumentAnswerer(
                primary_answerer=llm_answerer,
                fallback_answerer=rule_answerer,
            )

        return llm_answerer

    raise ValueError(
        "Unsupported DOCUMENT_ANSWERER_TYPE. "
        "Supported values: rule, llm."
    )
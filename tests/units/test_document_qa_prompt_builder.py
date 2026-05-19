from services.document_qa_prompt_builder import (
    RetrievedContextBlock,
    build_document_qa_prompt,
)


def test_build_document_qa_prompt_includes_grounding_rules_and_context():
    prompt = build_document_qa_prompt(
        question="What is the refund policy?",
        context_blocks=[
            RetrievedContextBlock(
                source_id=1,
                filename="policy.pdf",
                page_number=4,
                text="Refunds are available within 30 days of purchase.",
            )
        ],
    )

    assert "Answer only using the retrieved context" in prompt
    assert "Do not use outside knowledge" in prompt
    assert "What is the refund policy?" in prompt
    assert "[1] policy.pdf, page 4" in prompt
    assert "Refunds are available within 30 days of purchase." in prompt
    assert "Cite sources using [source_id]" in prompt


def test_build_document_qa_prompt_handles_missing_page_number():
    prompt = build_document_qa_prompt(
        question="Who handles billing?",
        context_blocks=[
            RetrievedContextBlock(
                source_id=2,
                filename="team_directory.txt",
                page_number=None,
                text="Billing questions are handled by the finance team.",
            )
        ],
    )

    assert "[2] team_directory.txt, page unavailable" in prompt
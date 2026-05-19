from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedContextBlock:
    source_id: int
    filename: str
    page_number: int | None
    text: str


def build_document_qa_prompt(
    question: str,
    context_blocks: list[RetrievedContextBlock],
) -> str:
    formatted_context = "\n\n".join(
        _format_context_block(block)
        for block in context_blocks
    )

    return f"""You are a document-grounded business knowledge-base assistant.

Rules:
- Answer only using the retrieved context below.
- Do not use outside knowledge.
- If the context does not contain the answer, say that the answer was not found in the uploaded documents.
- If the context is incomplete, answer only the supported part and clearly say what is missing.
- Cite sources using [source_id].
- Do not invent company policy, pricing, legal, HR, or support details.

Question:
{question}

Retrieved context:
{formatted_context}

Answer:
"""


def _format_context_block(block: RetrievedContextBlock) -> str:
    page_label = (
        f"page {block.page_number}"
        if block.page_number is not None
        else "page unavailable"
    )

    return (
        f"[{block.source_id}] {block.filename}, {page_label}\n"
        f"{block.text.strip()}"
    )
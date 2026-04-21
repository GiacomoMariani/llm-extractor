import pytest

from services.rule_based_summarizer import RuleBasedSummarizer


@pytest.mark.asyncio
async def test_rule_based_summarizer_returns_first_sentence():
    summarizer = RuleBasedSummarizer()

    result = await summarizer.summarize(
        "FastAPI is simple to start with. It is also good for APIs. Testing is important.",
        max_sentences=1,
    )

    assert result.summary == "FastAPI is simple to start with."


@pytest.mark.asyncio
async def test_rule_based_summarizer_returns_first_two_sentences():
    summarizer = RuleBasedSummarizer()

    result = await summarizer.summarize(
        "FastAPI is simple to start with. It is also good for APIs. Testing is important.",
        max_sentences=2,
    )

    assert result.summary == (
        "FastAPI is simple to start with. It is also good for APIs."
    )
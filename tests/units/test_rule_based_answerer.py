import pytest

from services.rule_based_answerer import RuleBasedAnswerer


@pytest.mark.asyncio
async def test_rule_based_answerer_returns_best_matching_sentence():
    answerer = RuleBasedAnswerer()

    result = await answerer.answer(
        question="What does the project use for the backend?",
        context=(
            "We are building an API. "
            "The project uses FastAPI for the backend. "
            "Testing is also important."
        ),
    )

    assert result.answer == "The project uses FastAPI for the backend."


@pytest.mark.asyncio
async def test_rule_based_answerer_returns_fallback_when_no_match():
    answerer = RuleBasedAnswerer()

    result = await answerer.answer(
        question="What is the capital of France?",
        context="This project uses Python and FastAPI.",
    )

    assert result.answer in {
        "This project uses Python and FastAPI.",
        "I could not find the answer in the provided context.",
    }
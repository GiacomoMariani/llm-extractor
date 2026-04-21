import pytest

from services.rule_based_router import RuleBasedRouter


@pytest.mark.asyncio
async def test_rule_based_router_returns_extract():
    router = RuleBasedRouter()

    result = await router.route("Please extract the email and order id from this text.")

    assert result.route == "extract"


@pytest.mark.asyncio
async def test_rule_based_router_returns_classify():
    router = RuleBasedRouter()

    result = await router.route("Please classify this support ticket.")

    assert result.route == "classify"


@pytest.mark.asyncio
async def test_rule_based_router_returns_summarize():
    router = RuleBasedRouter()

    result = await router.route("Can you summarize this article?")

    assert result.route == "summarize"


@pytest.mark.asyncio
async def test_rule_based_router_returns_answer():
    router = RuleBasedRouter()

    result = await router.route("What framework are we using?")

    assert result.route == "answer"
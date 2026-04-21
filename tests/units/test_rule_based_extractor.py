import pytest

from services.rule_based_extractor import RuleBasedExtractor


@pytest.mark.asyncio
async def test_rule_based_extractor_extracts_expected_fields():
    extractor = RuleBasedExtractor()

    result = await extractor.extract(
        "Hi, my email is marco.rossi@example.com. "
        "I need a refund for ORD-12345. This is urgent."
    )

    assert result.email == "marco.rossi@example.com"
    assert result.order_id == "ORD-12345"
    assert result.urgency == "high"
    assert result.has_refund_request is True


@pytest.mark.asyncio
async def test_rule_based_extractor_handles_missing_fields():
    extractor = RuleBasedExtractor()

    result = await extractor.extract("Hello, please help me when possible.")

    assert result.email is None
    assert result.order_id is None
    assert result.urgency == "medium"
    assert result.has_refund_request is False
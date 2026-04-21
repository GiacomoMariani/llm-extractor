import pytest

from services.rule_based_classifier import RuleBasedClassifier


@pytest.mark.asyncio
async def test_rule_based_classifier_returns_refund():
    classifier = RuleBasedClassifier()

    result = await classifier.classify("I want a refund for my purchase.")

    assert result.category == "refund"


@pytest.mark.asyncio
async def test_rule_based_classifier_returns_billing():
    classifier = RuleBasedClassifier()

    result = await classifier.classify("There is a strange charge on my invoice.")

    assert result.category == "billing"


@pytest.mark.asyncio
async def test_rule_based_classifier_returns_technical():
    classifier = RuleBasedClassifier()

    result = await classifier.classify("The app crashes when I log in.")

    assert result.category == "technical"


@pytest.mark.asyncio
async def test_rule_based_classifier_returns_general():
    classifier = RuleBasedClassifier()

    result = await classifier.classify("Hello, I have a question about your service.")

    assert result.category == "general"
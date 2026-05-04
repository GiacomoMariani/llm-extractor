import pytest

from services.usage_tracking_service import (
    SQLiteUsageTrackingService,
    UsagePricing,
)


def test_estimate_usage_counts_input_and_output_tokens(tmp_path):
    service = SQLiteUsageTrackingService(str(tmp_path / "test_usage.db"))

    estimate = service.estimate_usage(
        input_text="FastAPI is the backend framework.",
        output_text="FastAPI.",
        pricing=UsagePricing(
            input_cost_per_1k_tokens_usd=0.10,
            output_cost_per_1k_tokens_usd=0.20,
        ),
    )

    assert estimate.input_tokens > 0
    assert estimate.output_tokens > 0
    assert estimate.estimated_cost_usd > 0


def test_record_usage_stores_estimated_usage_record(tmp_path):
    service = SQLiteUsageTrackingService(str(tmp_path / "test_usage.db"))

    record = service.record_usage(
        operation="document_answer",
        provider="local",
        model_name="rule-based-answerer",
        input_text="What backend framework is used?",
        output_text="FastAPI is used.",
        pricing=UsagePricing(
            input_cost_per_1k_tokens_usd=0.10,
            output_cost_per_1k_tokens_usd=0.20,
        ),
        metadata={
            "document_id": "doc-123",
            "request_id": "req-abc",
        },
    )

    assert record.usage_id.startswith("usage-")
    assert record.operation == "document_answer"
    assert record.provider == "local"
    assert record.model_name == "rule-based-answerer"
    assert record.input_tokens > 0
    assert record.output_tokens > 0
    assert record.estimated_cost_usd > 0
    assert record.metadata == {
        "document_id": "doc-123",
        "request_id": "req-abc",
    }
    assert record.created_at


def test_list_recent_usage_returns_newest_records_first(tmp_path):
    service = SQLiteUsageTrackingService(str(tmp_path / "test_usage.db"))

    first_record = service.record_usage_tokens(
        operation="embedding",
        provider="local",
        model_name="local-embedding",
        input_tokens=10,
        output_tokens=0,
        estimated_cost_usd=0.01,
    )

    second_record = service.record_usage_tokens(
        operation="document_answer",
        provider="local",
        model_name="rule-based-answerer",
        input_tokens=20,
        output_tokens=5,
        estimated_cost_usd=0.02,
    )

    records = service.list_recent_usage(limit=10)

    assert len(records) == 2
    assert records[0].usage_id == second_record.usage_id
    assert records[1].usage_id == first_record.usage_id


def test_list_recent_usage_respects_limit(tmp_path):
    service = SQLiteUsageTrackingService(str(tmp_path / "test_usage.db"))

    service.record_usage_tokens(
        operation="one",
        provider="local",
        model_name="test-model",
        input_tokens=1,
        output_tokens=0,
        estimated_cost_usd=0.01,
    )

    service.record_usage_tokens(
        operation="two",
        provider="local",
        model_name="test-model",
        input_tokens=1,
        output_tokens=0,
        estimated_cost_usd=0.01,
    )

    records = service.list_recent_usage(limit=1)

    assert len(records) == 1


def test_list_recent_usage_returns_empty_list_for_zero_limit(tmp_path):
    service = SQLiteUsageTrackingService(str(tmp_path / "test_usage.db"))

    service.record_usage_tokens(
        operation="embedding",
        provider="local",
        model_name="local-embedding",
        input_tokens=10,
        output_tokens=0,
        estimated_cost_usd=0.01,
    )

    records = service.list_recent_usage(limit=0)

    assert records == []


def test_get_total_estimated_cost_usd_returns_sum(tmp_path):
    service = SQLiteUsageTrackingService(str(tmp_path / "test_usage.db"))

    service.record_usage_tokens(
        operation="embedding",
        provider="local",
        model_name="local-embedding",
        input_tokens=10,
        output_tokens=0,
        estimated_cost_usd=0.01,
    )

    service.record_usage_tokens(
        operation="document_answer",
        provider="local",
        model_name="rule-based-answerer",
        input_tokens=20,
        output_tokens=5,
        estimated_cost_usd=0.02,
    )

    assert service.get_total_estimated_cost_usd() == 0.03


def test_record_usage_tokens_rejects_negative_input_tokens(tmp_path):
    service = SQLiteUsageTrackingService(str(tmp_path / "test_usage.db"))

    with pytest.raises(
        ValueError,
        match="input_tokens must be greater than or equal to 0.",
    ):
        service.record_usage_tokens(
            operation="embedding",
            provider="local",
            model_name="local-embedding",
            input_tokens=-1,
            output_tokens=0,
            estimated_cost_usd=0.0,
        )


def test_record_usage_tokens_rejects_negative_output_tokens(tmp_path):
    service = SQLiteUsageTrackingService(str(tmp_path / "test_usage.db"))

    with pytest.raises(
        ValueError,
        match="output_tokens must be greater than or equal to 0.",
    ):
        service.record_usage_tokens(
            operation="document_answer",
            provider="local",
            model_name="rule-based-answerer",
            input_tokens=1,
            output_tokens=-1,
            estimated_cost_usd=0.0,
        )


def test_record_usage_tokens_rejects_negative_cost(tmp_path):
    service = SQLiteUsageTrackingService(str(tmp_path / "test_usage.db"))

    with pytest.raises(
        ValueError,
        match="estimated_cost_usd must be greater than or equal to 0.",
    ):
        service.record_usage_tokens(
            operation="document_answer",
            provider="local",
            model_name="rule-based-answerer",
            input_tokens=1,
            output_tokens=1,
            estimated_cost_usd=-0.01,
        )


def test_clear_removes_usage_records(tmp_path):
    service = SQLiteUsageTrackingService(str(tmp_path / "test_usage.db"))

    service.record_usage_tokens(
        operation="embedding",
        provider="local",
        model_name="local-embedding",
        input_tokens=10,
        output_tokens=0,
        estimated_cost_usd=0.01,
    )

    service.clear()

    assert service.list_recent_usage() == []
    assert service.get_total_estimated_cost_usd() == 0.0
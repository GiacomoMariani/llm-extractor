import pytest

from settings import get_settings


def test_get_settings_reads_uploaded_text_config(monkeypatch):
    monkeypatch.setenv("APP_UPLOADED_TEXT_DB_PATH", "custom_uploads.db")
    monkeypatch.setenv("APP_UPLOADED_TEXT_CLEANUP_MAX_AGE_HOURS", "48")

    settings = get_settings()

    assert settings.uploaded_text_db_path == "custom_uploads.db"
    assert settings.uploaded_text_cleanup_max_age_hours == 48


@pytest.mark.parametrize("value", ["0", "-1", "721", "not-an-int"])
def test_get_settings_rejects_invalid_uploaded_text_cleanup_age(
    monkeypatch,
    value: str,
):
    monkeypatch.setenv("APP_UPLOADED_TEXT_CLEANUP_MAX_AGE_HOURS", value)

    with pytest.raises(ValueError):
        get_settings()


def test_get_settings_uses_rule_document_answerer_by_default(monkeypatch):
    monkeypatch.delenv("DOCUMENT_ANSWERER_TYPE", raising=False)

    settings = get_settings()

    assert settings.document_answerer_type == "rule"


def test_get_settings_reads_document_answerer_type(monkeypatch):
    monkeypatch.setenv("DOCUMENT_ANSWERER_TYPE", "LLM")

    settings = get_settings()

    assert settings.document_answerer_type == "llm"

def test_get_settings_uses_fake_document_qa_model_client_by_default(monkeypatch):
    monkeypatch.delenv("DOCUMENT_QA_MODEL_CLIENT_TYPE", raising=False)
    monkeypatch.delenv("DOCUMENT_QA_MODEL_NAME", raising=False)

    settings = get_settings()

    assert settings.document_qa_model_client_type == "fake"
    assert settings.document_qa_model_name == "fake-document-qa"


def test_get_settings_reads_document_qa_model_client_config(monkeypatch):
    monkeypatch.setenv("DOCUMENT_QA_MODEL_CLIENT_TYPE", "OPENAI")
    monkeypatch.setenv("DOCUMENT_QA_MODEL_NAME", "gpt-4.1-mini")

    settings = get_settings()

    assert settings.document_qa_model_client_type == "openai"
    assert settings.document_qa_model_name == "gpt-4.1-mini"

def test_get_settings_enables_document_qa_rule_fallback_by_default(monkeypatch):
    monkeypatch.delenv("DOCUMENT_QA_FALLBACK_TO_RULE", raising=False)

    settings = get_settings()

    assert settings.document_qa_fallback_to_rule is True


def test_get_settings_reads_document_qa_rule_fallback(monkeypatch):
    monkeypatch.setenv("DOCUMENT_QA_FALLBACK_TO_RULE", "false")

    settings = get_settings()

    assert settings.document_qa_fallback_to_rule is False


def test_get_settings_rejects_invalid_document_qa_rule_fallback(monkeypatch):
    monkeypatch.setenv("DOCUMENT_QA_FALLBACK_TO_RULE", "maybe")

    try:
        get_settings()
    except ValueError as ex:
        assert "DOCUMENT_QA_FALLBACK_TO_RULE" in str(ex)
    else:
        raise AssertionError("Expected ValueError.")
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
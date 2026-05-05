import sqlite3

from fastapi.testclient import TestClient

import main
from main import app
from services.uploaded_text_store import SQLiteUploadedTextStore

client = TestClient(app)

AUTH_HEADERS = {"X-API-Key": "test-secret-key"}


def test_cleanup_uploaded_texts_requires_api_key():
    response = client.post(
        "/admin/uploaded-texts/cleanup",
        json={"max_age_hours": 24},
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or missing API key."
    }


def test_cleanup_uploaded_texts_deletes_only_stale_rows(tmp_path):
    text_store = SQLiteUploadedTextStore(tmp_path / "uploaded_texts.db")

    old_content_id = text_store.save_text(
        filename="old.txt",
        text="old staged upload",
    )
    fresh_content_id = text_store.save_text(
        filename="fresh.txt",
        text="fresh staged upload",
    )

    with sqlite3.connect(tmp_path / "uploaded_texts.db") as connection:
        connection.execute(
            """
            UPDATE uploaded_texts
            SET created_at = datetime('now', '-25 hours')
            WHERE content_id = ?
            """,
            (old_content_id,),
        )
        connection.execute(
            """
            UPDATE uploaded_texts
            SET created_at = datetime('now', '-23 hours')
            WHERE content_id = ?
            """,
            (fresh_content_id,),
        )
        connection.commit()

    main.app.dependency_overrides[main.get_uploaded_text_store] = lambda: text_store

    try:
        response = client.post(
            "/admin/uploaded-texts/cleanup",
            headers=AUTH_HEADERS,
            json={"max_age_hours": 24},
        )
    finally:
        main.app.dependency_overrides.pop(main.get_uploaded_text_store, None)

    assert response.status_code == 200
    assert response.json() == {"deleted_count": 1}
    assert text_store.get_text(old_content_id) is None
    assert text_store.get_text(fresh_content_id) == "fresh staged upload"


def test_cleanup_uploaded_texts_rejects_invalid_max_age():
    response = client.post(
        "/admin/uploaded-texts/cleanup",
        headers=AUTH_HEADERS,
        json={"max_age_hours": 0},
    )

    assert response.status_code == 422

def test_cleanup_uploaded_texts_uses_configured_default_max_age(
    tmp_path,
    monkeypatch,
):
    text_store = SQLiteUploadedTextStore(tmp_path / "uploaded_texts.db")

    old_content_id = text_store.save_text(
        filename="old.txt",
        text="old staged upload",
    )
    fresh_content_id = text_store.save_text(
        filename="fresh.txt",
        text="fresh staged upload",
    )

    with sqlite3.connect(tmp_path / "uploaded_texts.db") as connection:
        connection.execute(
            """
            UPDATE uploaded_texts
            SET created_at = datetime('now', '-13 hours')
            WHERE content_id = ?
            """,
            (old_content_id,),
        )
        connection.execute(
            """
            UPDATE uploaded_texts
            SET created_at = datetime('now', '-11 hours')
            WHERE content_id = ?
            """,
            (fresh_content_id,),
        )
        connection.commit()

    monkeypatch.setenv("APP_UPLOADED_TEXT_CLEANUP_MAX_AGE_HOURS", "12")

    main.app.dependency_overrides[main.get_uploaded_text_store] = lambda: text_store

    try:
        response = client.post(
            "/admin/uploaded-texts/cleanup",
            headers=AUTH_HEADERS,
            json={},
        )
    finally:
        main.app.dependency_overrides.pop(main.get_uploaded_text_store, None)

    assert response.status_code == 200
    assert response.json() == {"deleted_count": 1}
    assert text_store.get_text(old_content_id) is None
    assert text_store.get_text(fresh_content_id) == "fresh staged upload"
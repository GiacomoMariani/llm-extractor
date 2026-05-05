from services.uploaded_text_store import SQLiteUploadedTextStore


def test_sqlite_uploaded_text_store_saves_and_reads_text(tmp_path):
    store = SQLiteUploadedTextStore(tmp_path / "uploaded_texts.db")

    content_id = store.save_text(
        filename="guide.txt",
        text="FastAPI is the backend framework.",
    )

    assert content_id

    assert store.get_text(content_id) == "FastAPI is the backend framework."


def test_sqlite_uploaded_text_store_returns_none_for_missing_content(tmp_path):
    store = SQLiteUploadedTextStore(tmp_path / "uploaded_texts.db")

    assert store.get_text("missing-content-id") is None


def test_sqlite_uploaded_text_store_deletes_text(tmp_path):
    store = SQLiteUploadedTextStore(tmp_path / "uploaded_texts.db")

    content_id = store.save_text(
        filename="guide.txt",
        text="FastAPI is the backend framework.",
    )

    assert store.get_text(content_id) == "FastAPI is the backend framework."

    assert store.delete_text(content_id) is True
    assert store.get_text(content_id) is None
    assert store.delete_text(content_id) is False

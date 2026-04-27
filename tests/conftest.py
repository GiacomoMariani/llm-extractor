import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import main
from services.sqlite_document_store import SQLiteDocumentStore


@pytest.fixture(autouse=True)
def use_test_sqlite_store(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test_app.db"
    test_store = SQLiteDocumentStore(str(test_db_path))

    monkeypatch.setattr(main, "sqlite_document_store", test_store)

    yield

    test_store.clear()

@pytest.fixture(autouse=True)
def set_test_api_key(monkeypatch):
    monkeypatch.setenv("APP_API_KEY", "test-secret-key")
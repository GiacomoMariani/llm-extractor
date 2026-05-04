import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import main
from services.evaluation_result_store import SQLiteEvaluationResultStore
from services.ingestion_job_store import SQLiteIngestionJobStore
from services.sqlite_document_store import SQLiteDocumentStore
from services.usage_tracking_service import SQLiteUsageTrackingService


@pytest.fixture(autouse=True)
def use_test_sqlite_store(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test_app.db"

    test_store = SQLiteDocumentStore(str(test_db_path))
    test_job_store = SQLiteIngestionJobStore(str(test_db_path))
    test_evaluation_result_store = SQLiteEvaluationResultStore(str(test_db_path))
    test_usage_tracking_service = SQLiteUsageTrackingService(str(test_db_path))

    monkeypatch.setattr(main, "sqlite_document_store", test_store)
    monkeypatch.setattr(main, "sqlite_ingestion_job_store", test_job_store)
    monkeypatch.setattr(
        main,
        "sqlite_evaluation_result_store",
        test_evaluation_result_store,
    )
    monkeypatch.setattr(
        main,
        "sqlite_usage_tracking_service",
        test_usage_tracking_service,
    )

    yield

    test_usage_tracking_service.clear()
    test_evaluation_result_store.clear()
    test_job_store.clear()
    test_store.clear()


@pytest.fixture(autouse=True)
def set_test_api_key(monkeypatch):
    monkeypatch.setenv("APP_API_KEY", "test-secret-key")
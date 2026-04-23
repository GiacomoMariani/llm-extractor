import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.document_store import document_store  # noqa: E402


@pytest.fixture(autouse=True)
def clear_document_store():
    document_store.clear()
    yield
    document_store.clear()
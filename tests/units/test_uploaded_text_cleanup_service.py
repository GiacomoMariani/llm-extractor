from datetime import datetime, timezone

import pytest

from services.uploaded_text_cleanup_service import delete_stale_uploaded_texts


class RecordingUploadedTextStore:
    def __init__(self) -> None:
        self.cutoff: datetime | None = None

    def save_text(self, filename: str, text: str) -> str:
        raise NotImplementedError

    def get_text(self, content_id: str) -> str | None:
        raise NotImplementedError

    def delete_text(self, content_id: str) -> bool:
        raise NotImplementedError

    def delete_texts_created_before(self, cutoff: datetime) -> int:
        self.cutoff = cutoff
        return 3


def test_delete_stale_uploaded_texts_uses_max_age_as_cutoff() -> None:
    store = RecordingUploadedTextStore()

    deleted_count = delete_stale_uploaded_texts(
        uploaded_text_store=store,
        max_age_hours=24,
        now=datetime(2024, 1, 3, 12, 0, 0, tzinfo=timezone.utc),
    )

    assert deleted_count == 3
    assert store.cutoff == datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize("max_age_hours", [0, -1])
def test_delete_stale_uploaded_texts_rejects_non_positive_retention(
    max_age_hours: int,
) -> None:
    store = RecordingUploadedTextStore()

    with pytest.raises(ValueError, match="max_age_hours must be greater than 0."):
        delete_stale_uploaded_texts(
            uploaded_text_store=store,
            max_age_hours=max_age_hours,
            now=datetime(2024, 1, 3, 12, 0, 0, tzinfo=timezone.utc),
        )
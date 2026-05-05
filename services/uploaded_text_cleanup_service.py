from __future__ import annotations

from datetime import datetime, timedelta, timezone

from services.uploaded_text_store import UploadedTextStore


def delete_stale_uploaded_texts(
    uploaded_text_store: UploadedTextStore,
    max_age_hours: int,
    now: datetime | None = None,
) -> int:
    if max_age_hours <= 0:
        raise ValueError("max_age_hours must be greater than 0.")

    reference_time = now or datetime.now(timezone.utc)
    cutoff = reference_time - timedelta(hours=max_age_hours)

    return uploaded_text_store.delete_texts_created_before(cutoff)
"""Tests for tracker heading persistence on contacts."""

import pytest

from app.models import ContactUpsert
from app.repository.contacts import ContactRepository


@pytest.mark.asyncio
async def test_contact_upsert_persists_tracker_heading(test_db):
    public_key = "aa" * 32
    await ContactRepository.upsert(
        ContactUpsert(
            public_key=public_key,
            name="Tracker One",
            type=1,
            lat=52.0,
            lon=5.0,
            is_tracker=True,
            tracker_name="Van-1",
            tracker_heading=90.0,
        )
    )

    contact = await ContactRepository.get_by_key(public_key)
    assert contact is not None
    assert contact.is_tracker is True
    assert contact.tracker_name == "Van-1"
    assert contact.tracker_heading == pytest.approx(90.0)

    await ContactRepository.upsert(
        ContactUpsert(
            public_key=public_key,
            tracker_heading=180.0,
        )
    )
    updated = await ContactRepository.get_by_key(public_key)
    assert updated is not None
    assert updated.tracker_heading == pytest.approx(180.0)
    assert updated.is_tracker is True

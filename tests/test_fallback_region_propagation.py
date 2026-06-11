"""
Test that region_name is correctly propagated in fallback message paths.

This tests the fix for the issue where the raw packet feed shows region "nl"
but bots see "no scope" because the fallback event handler path wasn't
propagating region_name from stored raw packets.
"""
import time
from typing import Any

import pytest

from app.repository import ChannelRepository, ContactRepository, RawPacketRepository
from app.services.dm_ingest import ingest_fallback_direct_message
from app.services.messages import create_fallback_channel_message


@pytest.mark.asyncio
async def test_fallback_dm_propagates_region_from_stored_packet(test_db):
    """Test that fallback DM ingest finds and uses region from stored raw packet."""
    # Setup: Create a contact
    contact_key = "a" * 64
    await ContactRepository.upsert({
        "public_key": contact_key,
        "name": "TestContact",
        "type": 1,
    })

    # Store a raw packet with region "nl"
    raw_packet_data = bytes.fromhex("0102030405")  # Dummy packet
    sender_ts = int(time.time())
    packet_id, _ = await RawPacketRepository.create(
        data=raw_packet_data,
        timestamp=sender_ts,
        region_name="nl",
    )

    # Track broadcast calls
    broadcast_calls: list[tuple[str, dict]] = []

    def mock_broadcast(event_type: str, data: dict, **kwargs) -> None:
        broadcast_calls.append((event_type, data))

    # Simulate fallback DM ingestion (from CONTACT_MSG_RECV event)
    # This doesn't have packet_id, so it should look up by timestamp
    message = await ingest_fallback_direct_message(
        conversation_key=contact_key,
        text="Hello from fallback",
        sender_timestamp=sender_ts,  # Same timestamp as raw packet
        received_at=sender_ts,
        path=None,
        path_len=None,
        txt_type=0,
        signature=None,
        sender_name="TestContact",
        sender_key=contact_key,
        broadcast_fn=mock_broadcast,
        update_last_contacted_key=contact_key,
    )

    assert message is not None
    assert len(broadcast_calls) > 0

    # Find the message broadcast
    message_broadcasts = [call for call in broadcast_calls if call[0] == "message"]
    assert len(message_broadcasts) == 1

    event_type, event_data = message_broadcasts[0]
    # The broadcast should include region_name from the stored packet
    assert event_data.get("region_name") == "nl", \
        f"Expected region_name='nl', got {event_data.get('region_name')}"


@pytest.mark.asyncio
async def test_fallback_channel_propagates_region_from_stored_packet(test_db):
    """Test that fallback channel message ingest finds and uses region from stored raw packet."""
    # Setup: Create a channel
    channel_key = "b" * 32
    await ChannelRepository.upsert(
        key=channel_key,
        name="TestChannel",
    )

    # Store a raw packet with region "us"
    raw_packet_data = bytes.fromhex("0a0b0c0d0e")  # Dummy packet
    sender_ts = int(time.time())
    packet_id, _ = await RawPacketRepository.create(
        data=raw_packet_data,
        timestamp=sender_ts,
        region_name="us",
    )

    # Track broadcast calls
    broadcast_calls: list[tuple[str, dict]] = []

    def mock_broadcast(event_type: str, data: dict, **kwargs) -> None:
        broadcast_calls.append((event_type, data))

    # Simulate fallback channel message ingestion
    message = await create_fallback_channel_message(
        conversation_key=channel_key,
        message_text="Hello channel",
        sender_timestamp=sender_ts,  # Same timestamp as raw packet
        received_at=sender_ts,
        path=None,
        path_len=None,
        txt_type=0,
        sender_name="SomeSender",
        channel_name="TestChannel",
        broadcast_fn=mock_broadcast,
    )

    assert message is not None
    assert len(broadcast_calls) > 0

    # Find the message broadcast
    message_broadcasts = [call for call in broadcast_calls if call[0] == "message"]
    assert len(message_broadcasts) == 1

    event_type, event_data = message_broadcasts[0]
    # The broadcast should include region_name from the stored packet
    assert event_data.get("region_name") == "us", \
        f"Expected region_name='us', got {event_data.get('region_name')}"


@pytest.mark.asyncio
async def test_fallback_message_no_matching_packet_still_works(test_db):
    """Test that fallback messages work even when no matching packet is found."""
    # Setup: Create a contact
    contact_key = "c" * 64
    await ContactRepository.upsert({
        "public_key": contact_key,
        "name": "TestContact2",
        "type": 1,
    })

    broadcast_calls: list[tuple[str, dict]] = []

    def mock_broadcast(event_type: str, data: dict, **kwargs) -> None:
        broadcast_calls.append((event_type, data))

    # Ingest fallback DM with timestamp that doesn't match any stored packet
    far_future_ts = int(time.time()) + 3600
    message = await ingest_fallback_direct_message(
        conversation_key=contact_key,
        text="No matching packet",
        sender_timestamp=far_future_ts,
        received_at=far_future_ts,
        path=None,
        path_len=None,
        txt_type=0,
        signature=None,
        sender_name="TestContact2",
        sender_key=contact_key,
        broadcast_fn=mock_broadcast,
        update_last_contacted_key=contact_key,
    )

    # Message should still be created, just without region_name
    assert message is not None
    message_broadcasts = [call for call in broadcast_calls if call[0] == "message"]
    assert len(message_broadcasts) == 1
    
    event_type, event_data = message_broadcasts[0]
    # region_name should be None or absent
    assert event_data.get("region_name") is None


@pytest.mark.asyncio
async def test_raw_packet_timestamp_proximity_lookup(test_db):
    """Test the RawPacketRepository.find_by_timestamp_proximity method."""
    # Create several packets at different times
    base_ts = int(time.time())
    
    packet1_id, _ = await RawPacketRepository.create(
        data=bytes.fromhex("aa"),
        timestamp=base_ts,
        region_name="region1",
    )
    
    packet2_id, _ = await RawPacketRepository.create(
        data=bytes.fromhex("bb"),
        timestamp=base_ts + 2,  # 2 seconds later
        region_name="region2",
    )
    
    packet3_id, _ = await RawPacketRepository.create(
        data=bytes.fromhex("cc"),
        timestamp=base_ts + 10,  # 10 seconds later
        region_name="region3",
    )

    # Find packet close to base_ts (should match packet1)
    result = await RawPacketRepository.find_by_timestamp_proximity(
        timestamp=base_ts,
        window_seconds=5,
    )
    assert result is not None
    assert result["id"] == packet1_id
    assert result["region_name"] == "region1"

    # Find packet close to base_ts + 2 (should match packet2)
    result = await RawPacketRepository.find_by_timestamp_proximity(
        timestamp=base_ts + 2,
        window_seconds=5,
    )
    assert result is not None
    assert result["id"] == packet2_id
    assert result["region_name"] == "region2"

    # Find packet close to base_ts + 1 (should match packet1, closer than packet2)
    result = await RawPacketRepository.find_by_timestamp_proximity(
        timestamp=base_ts + 1,
        window_seconds=5,
    )
    assert result is not None
    assert result["id"] == packet1_id
    assert result["region_name"] == "region1"

    # Find packet with narrow window (should not match packet3)
    result = await RawPacketRepository.find_by_timestamp_proximity(
        timestamp=base_ts,
        window_seconds=3,
    )
    assert result is not None
    # Should match packet1, not packet3
    assert result["id"] == packet1_id

    # Find packet far from any stored packet
    result = await RawPacketRepository.find_by_timestamp_proximity(
        timestamp=base_ts + 1000,
        window_seconds=5,
    )
    assert result is None

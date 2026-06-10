"""Tests for geographic proximity filtering in path hop last_seen updates."""

import pytest

from app.packet_processor import _haversine_distance_km


class TestHaversineDistance:
    """Test geographic distance calculations."""

    def test_same_location(self):
        """Distance between same coordinates should be 0."""
        distance = _haversine_distance_km(37.7749, -122.4194, 37.7749, -122.4194)
        assert distance == 0.0

    def test_known_distance_sf_to_san_jose(self):
        """Test known distance: San Francisco to San Jose (~68km)."""
        # San Francisco
        sf_lat, sf_lon = 37.7749, -122.4194
        # San Jose
        sj_lat, sj_lon = 37.3387, -121.8853
        
        distance = _haversine_distance_km(sf_lat, sf_lon, sj_lat, sj_lon)
        
        # Should be approximately 68km (within 5km tolerance for simplicity)
        assert 63 < distance < 73

    def test_short_distance(self):
        """Test short distance (~5km)."""
        # Two points roughly 5km apart
        lat1, lon1 = 40.7128, -74.0060
        lat2, lon2 = 40.7500, -74.0060
        
        distance = _haversine_distance_km(lat1, lon1, lat2, lon2)
        
        # Should be around 4-5km
        assert 3 < distance < 6

    def test_typical_lora_range(self):
        """Test typical LoRa hop distance (~10km)."""
        # Two points roughly 10km apart
        lat1, lon1 = 51.5074, -0.1278  # London
        lat2, lon2 = 51.6074, -0.1278  # ~11km north
        
        distance = _haversine_distance_km(lat1, lon1, lat2, lon2)
        
        # Should be around 10-11km
        assert 9 < distance < 13

    def test_beyond_threshold(self):
        """Test distance beyond 15km threshold."""
        # Two points ~50km apart
        lat1, lon1 = 48.8566, 2.3522   # Paris
        lat2, lon2 = 48.8566, 3.0000   # ~50km east
        
        distance = _haversine_distance_km(lat1, lon1, lat2, lon2)
        
        # Should be well beyond 15km
        assert distance > 15.0


@pytest.mark.asyncio
class TestGeographicPathFiltering:
    """Test geographic proximity filtering for path hops."""

    async def test_unambiguous_close_hops_updated(self, test_db):
        """When hops are unambiguous and close together, both should be updated."""
        from app.packet_processor import _update_last_seen_for_path_hops
        from app.repository.contacts import ContactRepository
        from app.models import ContactUpsert
        
        # Create two contacts 10km apart (within 15km threshold)
        await ContactRepository.upsert(ContactUpsert(
            public_key="a1" + "0" * 62,
            name="Repeater1",
            lat=40.7128,
            lon=-74.0060,
        ))
        await ContactRepository.upsert(ContactUpsert(
            public_key="b2" + "0" * 62,
            name="Repeater2",
            lat=40.7500,  # ~4km north
            lon=-74.0060,
        ))
        
        # Simulate a 2-byte path: a1b2
        await _update_last_seen_for_path_hops(
            path_hex="a1b2",
            hop_count=2,
            hash_size=1,
            timestamp=1000,
        )
        
        # Both should be updated
        updated1 = await ContactRepository.get_by_key("a1" + "0" * 62)
        updated2 = await ContactRepository.get_by_key("b2" + "0" * 62)
        
        assert updated1 is not None
        assert updated2 is not None
        assert updated1.last_seen == 1000
        assert updated2.last_seen == 1000

    async def test_distant_hops_filtered(self, test_db):
        """When hops are far apart (>15km), second hop should be filtered."""
        from app.packet_processor import _update_last_seen_for_path_hops
        from app.repository.contacts import ContactRepository
        from app.models import ContactUpsert
        
        # Create two contacts 50km apart (beyond 15km threshold)
        await ContactRepository.upsert(ContactUpsert(
            public_key="c3" + "0" * 62,
            name="Repeater1",
            lat=48.8566,
            lon=2.3522,
        ))
        await ContactRepository.upsert(ContactUpsert(
            public_key="d4" + "0" * 62,
            name="Repeater2",
            lat=48.8566,
            lon=3.0000,  # ~50km east
        ))
        
        # Simulate a path: c3d4
        await _update_last_seen_for_path_hops(
            path_hex="c3d4",
            hop_count=2,
            hash_size=1,
            timestamp=2000,
        )
        
        # First hop should be updated, second should be filtered
        updated1 = await ContactRepository.get_by_key("c3" + "0" * 62)
        updated2 = await ContactRepository.get_by_key("d4" + "0" * 62)
        
        assert updated1 is not None
        assert updated2 is not None
        assert updated1.last_seen == 2000
        assert updated2.last_seen is None  # Filtered out

    async def test_missing_gps_allowed(self, test_db):
        """When GPS data is missing, update should proceed (can't verify)."""
        from app.packet_processor import _update_last_seen_for_path_hops
        from app.repository.contacts import ContactRepository
        from app.models import ContactUpsert
        
        # Create one contact with GPS, one without
        await ContactRepository.upsert(ContactUpsert(
            public_key="e5" + "0" * 62,
            name="Repeater1",
            lat=40.7128,
            lon=-74.0060,
        ))
        await ContactRepository.upsert(ContactUpsert(
            public_key="f6" + "0" * 62,
            name="Repeater2",
            # No GPS data
        ))
        
        # Simulate a path: e5f6
        await _update_last_seen_for_path_hops(
            path_hex="e5f6",
            hop_count=2,
            hash_size=1,
            timestamp=3000,
        )
        
        # Both should be updated (can't verify distance without GPS)
        updated1 = await ContactRepository.get_by_key("e5" + "0" * 62)
        updated2 = await ContactRepository.get_by_key("f6" + "0" * 62)
        
        assert updated1 is not None
        assert updated2 is not None
        assert updated1.last_seen == 3000
        assert updated2.last_seen == 3000

    async def test_ambiguous_prefix_skipped(self, test_db):
        """When multiple contacts match a prefix, it should be skipped (ambiguous)."""
        from app.packet_processor import _update_last_seen_for_path_hops
        from app.repository.contacts import ContactRepository
        from app.models import ContactUpsert
        
        # Create two contacts with same 1-byte prefix
        await ContactRepository.upsert(ContactUpsert(
            public_key="aa11" + "0" * 60,
            name="Repeater1",
            lat=40.7128,
            lon=-74.0060,
        ))
        await ContactRepository.upsert(ContactUpsert(
            public_key="aa22" + "0" * 60,
            name="Repeater2",
            lat=40.7500,
            lon=-74.0060,
        ))
        
        # Simulate a path with ambiguous hop: aa
        await _update_last_seen_for_path_hops(
            path_hex="aa",
            hop_count=1,
            hash_size=1,
            timestamp=4000,
        )
        
        # Neither should be updated (ambiguous)
        updated1 = await ContactRepository.get_by_key("aa11" + "0" * 60)
        updated2 = await ContactRepository.get_by_key("aa22" + "0" * 60)
        
        assert updated1 is not None
        assert updated2 is not None
        assert updated1.last_seen is None
        assert updated2.last_seen is None

    async def test_three_hop_chain_with_outlier(self, test_db):
        """Test 3-hop path where middle hop is geographically impossible."""
        from app.packet_processor import _update_last_seen_for_path_hops
        from app.repository.contacts import ContactRepository
        from app.models import ContactUpsert
        
        # Create three contacts: two close (NY), one far (Paris)
        await ContactRepository.upsert(ContactUpsert(
            public_key="11" + "0" * 62,
            name="NYC1",
            lat=40.7128,
            lon=-74.0060,
        ))
        await ContactRepository.upsert(ContactUpsert(
            public_key="22" + "0" * 62,
            name="Paris",
            lat=48.8566,  # Paris - impossible middle hop
            lon=2.3522,
        ))
        await ContactRepository.upsert(ContactUpsert(
            public_key="33" + "0" * 62,
            name="NYC2",
            lat=40.7500,
            lon=-74.0060,
        ))
        
        # Simulate path: 11→22→33 (Paris in the middle is implausible)
        await _update_last_seen_for_path_hops(
            path_hex="112233",
            hop_count=3,
            hash_size=1,
            timestamp=5000,
        )
        
        updated1 = await ContactRepository.get_by_key("11" + "0" * 62)
        updated2 = await ContactRepository.get_by_key("22" + "0" * 62)
        updated3 = await ContactRepository.get_by_key("33" + "0" * 62)
        
        # First should be updated (no previous hop to check)
        assert updated1.last_seen == 5000
        # Second should be filtered (too far from first)
        assert updated2.last_seen is None
        # Third should also be filtered (no valid previous hop)
        assert updated3.last_seen is None

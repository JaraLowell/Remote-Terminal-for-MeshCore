"""Tests for progressive spam path narrowing helpers."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.services.spam_path_analysis import (
    estimate_origin_geo,
    hop_suspect_score,
    narrow_dominant_prefix,
    split_entry_partitioned_clusters,
    split_path_clusters,
)


@dataclass
class _PathRecord:
    full_rf_path: tuple[str, ...]


def test_narrow_dominant_prefix_deepens_when_paths_share_prefix():
    paths = [
        ("AA", "BB", "CC"),
        ("AA", "BB", "DD"),
        ("AA", "BB", "EE"),
        ("AA", "FF", "GG"),
    ]
    narrowed = narrow_dominant_prefix(paths, min_share=0.15)
    assert narrowed is not None
    assert narrowed.hop_tokens == ("AA", "BB")
    assert narrowed.packet_count == 3
    assert narrowed.traffic_share == pytest.approx(0.75)
    assert narrowed.narrowing_depth == 2


def test_split_path_clusters_peels_multiple_hotspots():
    records = [
        _PathRecord(("AA", "BB")),
        _PathRecord(("AA", "BB", "CC")),
        _PathRecord(("AA", "BB", "DD")),
        _PathRecord(("XX", "YY")),
        _PathRecord(("XX", "YY", "ZZ")),
        _PathRecord(("XX", "YY", "ZZ")),
    ]
    clusters = split_path_clusters(
        records,
        min_cluster_size=2,
        min_share=0.15,
        get_path=lambda record: record.full_rf_path,
    )
    assert len(clusters) == 2
    first_prefix = clusters[0][0].hop_tokens
    second_prefix = clusters[1][0].hop_tokens
    assert first_prefix[0] in {"AA", "XX"}
    assert second_prefix[0] in {"AA", "XX"}
    assert first_prefix != second_prefix


def test_split_entry_partitioned_clusters_handles_multi_source_floods():
    records = [
        _PathRecord(("AA", "11", "00")),
        _PathRecord(("AA", "11", "01")),
        _PathRecord(("AA", "11", "02")),
        _PathRecord(("BB", "22", "10")),
        _PathRecord(("BB", "22", "11")),
        _PathRecord(("BB", "22", "12")),
        _PathRecord(("CC", "33", "20")),
        _PathRecord(("CC", "33", "21")),
        _PathRecord(("CC", "33", "22")),
    ]
    clusters = split_entry_partitioned_clusters(
        records,
        min_cluster_size=3,
        min_share=0.15,
        get_path=lambda record: record.full_rf_path,
        max_clusters=3,
    )
    assert len(clusters) == 3
    prefixes = {cluster[0].hop_tokens for cluster in clusters}
    assert ("AA", "11") in prefixes
    assert ("BB", "22") in prefixes
    assert ("CC", "33") in prefixes
    assert all(cluster[0].traffic_share == pytest.approx(1 / 3) for cluster in clusters)


def test_estimate_origin_geo_prefers_source_side_hop():
    hop_geos = {
        "AA": {"lat": 52.0, "lon": 4.0, "name": "Ingress", "public_key": "aa" * 32},
        "BB": {"lat": 52.05, "lon": 4.05, "name": "Mid", "public_key": "bb" * 32},
    }
    origin = estimate_origin_geo(("AA", "BB"), hop_geos, max_hop_distance_km=10.0)
    assert origin is not None
    assert origin.hop == "AA"
    assert origin.name == "Ingress"
    assert origin.geo_chain_valid is True


def test_hop_suspect_score_favors_source_side_hops():
    observations = [
        ("AA", "BB"),
        ("AA", "CC"),
        ("BB", "AA"),
    ]
    assert hop_suspect_score("AA", observations) > hop_suspect_score("BB", observations)

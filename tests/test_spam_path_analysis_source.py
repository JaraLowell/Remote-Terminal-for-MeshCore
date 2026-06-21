"""Tests for dominant spam source detection helpers."""

from __future__ import annotations

from app.services.spam_path_analysis import (
    build_possibly_from_geo_hint,
    detect_dominant_packet_source,
    detect_dominant_path_source,
)


def test_detect_dominant_packet_source_requires_majority():
    candidate = detect_dominant_packet_source(
        ["hash1:AA", "hash1:AA", "hash1:AA", "hash1:BB"],
        min_share=0.5,
        min_count=3,
    )
    assert candidate is not None
    assert candidate.source_key == "hash1:AA"
    assert candidate.packet_count == 3
    assert candidate.kind == "packet"


def test_detect_dominant_path_source_uses_shared_prefix():
    candidate = detect_dominant_path_source(
        [("AA", "BB"), ("AA", "BB"), ("AA", "CC")],
        min_share=0.5,
        min_count=2,
    )
    assert candidate is not None
    assert candidate.source_label == "AA"
    assert candidate.kind == "path"


def test_build_possibly_from_geo_hint():
    hint = build_possibly_from_geo_hint("City-Repeater", "F6", 8.4)
    assert hint.startswith("Possibly from City-Repeater")
    assert "F6" in hint

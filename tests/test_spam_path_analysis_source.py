"""Tests for dominant spam source detection helpers."""

from __future__ import annotations

from app.services.spam_path_analysis import (
    build_possibly_from_geo_hint,
    build_source_filter_plan,
    detect_dominant_packet_source,
    detect_dominant_path_source,
    is_rotating_sender_identity,
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


def test_build_source_filter_plan_single_dominant_sender():
    plan = build_source_filter_plan(
        ["hash1:F0"] * 8 + ["hash1:AA", "hash1:BB"],
        min_share=0.5,
        min_count=3,
    )
    assert plan.mode == "single"
    assert plan.sources[0].source_label == "F0"
    assert plan.excluded_packets == 2


def test_build_source_filter_plan_dual_stable_senders():
    keys = ["hash1:F0"] * 6 + ["hash1:A1"] * 6
    plan = build_source_filter_plan(keys, min_share=0.5, min_count=3)
    assert plan.mode == "multi"
    assert {source.source_label for source in plan.sources} == {"F0", "A1"}


def test_build_source_filter_plan_rotating_sender_skips_filter():
    keys = [f"hash1:{byte:02X}" for byte in range(8)]
    assert is_rotating_sender_identity(keys, min_share=0.5)
    plan = build_source_filter_plan(keys, min_share=0.5, min_count=3)
    assert plan.mode == "rotating"

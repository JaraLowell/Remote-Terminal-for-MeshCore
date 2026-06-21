"""Tests for packet-level spam source extraction."""

from __future__ import annotations

from app.decoder import PacketInfo, PayloadType, RouteType
from app.services.spam_packet_source import extract_packet_source


def _packet(payload_type: PayloadType, payload: bytes) -> PacketInfo:
    return PacketInfo(
        route_type=RouteType.FLOOD,
        payload_type=payload_type,
        payload_version=0,
        path_length=0,
        path=b"",
        payload=payload,
    )


def test_extract_packet_source_reads_request_source_hash():
    payload = bytes([0x01, 0xAB, 0x00, 0x00]) + b"cipher"
    source = extract_packet_source(_packet(PayloadType.REQUEST, payload))
    assert source is not None
    assert source.source_key == "hash1:AB"
    assert source.source_label == "AB"


def test_extract_packet_source_reads_advert_public_key():
    public_key = bytes.fromhex("aa" * 32)
    payload = public_key + b"\x00" * 69
    source = extract_packet_source(_packet(PayloadType.ADVERT, payload))
    assert source is not None
    assert source.source_key == public_key.hex().upper()
    assert source.source_label == public_key.hex().upper()[:12]

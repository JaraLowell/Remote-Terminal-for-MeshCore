"""Extract stable packet-level source identity for spam flood analysis."""

from __future__ import annotations

from dataclasses import dataclass

from app.decoder import PacketInfo, PayloadType


@dataclass(frozen=True)
class PacketSourceIdentity:
    """Normalized sender identity extracted from a raw packet payload."""

    source_key: str
    source_label: str


def _hash1_source(payload: bytes) -> PacketSourceIdentity | None:
    if len(payload) < 2:
        return None
    source_hash = format(payload[1], "02x").upper()
    return PacketSourceIdentity(
        source_key=f"hash1:{source_hash}",
        source_label=source_hash,
    )


def extract_packet_source(packet_info: PacketInfo) -> PacketSourceIdentity | None:
    """Return a stable source key/label when the payload exposes sender identity."""
    payload = packet_info.payload
    if not payload:
        return None

    if packet_info.payload_type in {
        PayloadType.REQUEST,
        PayloadType.RESPONSE,
        PayloadType.TEXT_MESSAGE,
    }:
        return _hash1_source(payload)

    if packet_info.payload_type == PayloadType.ADVERT:
        if len(payload) < 32:
            return None
        public_key = payload[0:32].hex().upper()
        return PacketSourceIdentity(
            source_key=public_key,
            source_label=public_key[:12],
        )

    if packet_info.payload_type == PayloadType.ANON_REQUEST:
        if len(payload) < 33:
            return None
        public_key = payload[1:33].hex().upper()
        return PacketSourceIdentity(
            source_key=public_key,
            source_label=public_key[:12],
        )

    if packet_info.payload_type == PayloadType.CONTROL:
        # Control payloads vary; first byte is often subtype with pubkey later in body.
        if len(payload) < 33:
            return None
        public_key = payload[1:33].hex().upper()
        if public_key == "00" * 32:
            return None
        return PacketSourceIdentity(
            source_key=public_key,
            source_label=public_key[:12],
        )

    return None

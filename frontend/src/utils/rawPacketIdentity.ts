import type { RawPacket } from '../types';

/**
 * Get unique key for a raw packet.
 * For the raw packet feed, we use the DB row ID so the same packet (same payload)
 * updates the existing box as it propagates through different paths.
 * observation_id is used by stats tracking to count every RF observation.
 */
export function getRawPacketObservationKey(
  packet: Pick<RawPacket, 'id' | 'observation_id'>
): string {
  return `db-${packet.id}`;
}

export function appendRawPacketUnique(
  prev: RawPacket[],
  packet: RawPacket,
  maxPackets: number
): RawPacket[] {
  // Use DB row ID for deduplication - same packet updates existing box
  const existingIndex = prev.findIndex((p) => p.id === packet.id);
  
  if (existingIndex !== -1) {
    // Update existing packet with latest observation data
    const updated = [...prev];
    updated[existingIndex] = packet;
    return updated;
  }

  // New packet - append to end
  const updated = [...prev, packet];
  if (updated.length > maxPackets) {
    return updated.slice(-maxPackets);
  }
  return updated;
}

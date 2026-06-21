import { describe, expect, it } from 'vitest';
import {
  formatEpisodeLocationSummary,
  geoWeightedCentroid,
  resolveEpisodeLocationCoords,
} from '../utils/spamEpisodeLocation';
import type { SpamFloodCluster } from '../types';

function cluster(
  overrides: Partial<SpamFloodCluster> & Pick<SpamFloodCluster, 'packet_count'>,
): SpamFloodCluster {
  return {
    entry_hop: 'AA',
    entry_name: null,
    entry_public_key: null,
    lat: null,
    lon: null,
    dominant_route: 'AA',
    hop_tokens: [],
    refined_route: '',
    refined_hop_tokens: [],
    traffic_share: 0,
    concentration: 1,
    narrowing_depth: 1,
    confidence: 0,
    origin_hop: null,
    origin_name: null,
    origin_public_key: null,
    origin_lat: null,
    origin_lon: null,
    last_seen: 0,
    cluster_mode: null,
    ...overrides,
  };
}

describe('spamEpisodeLocation', () => {
  it('averages report cluster coordinates when primary hotspot has none', () => {
    const clusters = [
      cluster({ packet_count: 50, origin_lat: null, origin_lon: null }),
      cluster({ packet_count: 10, origin_lat: 40, origin_lon: -74 }),
      cluster({ packet_count: 30, origin_lat: 42, origin_lon: -76 }),
    ];

    const coords = resolveEpisodeLocationCoords(
      { primary_origin_lat: null, primary_origin_lon: null },
      clusters,
    );

    expect(coords).toEqual({ lat: 41.5, lon: -75.5 });
    expect(
      formatEpisodeLocationSummary(
        { primary_origin_lat: null, primary_origin_lon: null },
        clusters,
      ),
    ).toBe('41.500, -75.500');
  });

  it('prefers primary cluster coordinates over report average', () => {
    const clusters = [
      cluster({ packet_count: 50, origin_lat: 10, origin_lon: 20 }),
      cluster({ packet_count: 50, origin_lat: 30, origin_lon: 40 }),
    ];

    const coords = resolveEpisodeLocationCoords(
      { primary_origin_lat: null, primary_origin_lon: null },
      clusters,
    );

    expect(coords).toEqual({ lat: 10, lon: 20 });
  });

  it('weights centroid by packet count', () => {
    const centroid = geoWeightedCentroid([
      cluster({ packet_count: 1, origin_lat: 0, origin_lon: 0 }),
      cluster({ packet_count: 3, origin_lat: 30, origin_lon: 60 }),
    ]);

    expect(centroid).toEqual({ lat: 30, lon: 60 });
  });
});

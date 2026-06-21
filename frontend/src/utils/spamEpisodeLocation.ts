import type { SpamFloodCluster, SpamFloodEpisode } from '../types';

type GeoPoint = { lat: number; lon: number };

type ClusterGeoFields = Pick<
  SpamFloodCluster,
  'origin_lat' | 'origin_lon' | 'lat' | 'lon' | 'packet_count' | 'origin_geo_hint'
>;

type EpisodeGeoFields = Pick<SpamFloodEpisode, 'primary_origin_lat' | 'primary_origin_lon'>;

export function clusterGeoPoint(cluster: ClusterGeoFields): GeoPoint | null {
  const lat = cluster.origin_lat ?? cluster.lat;
  const lon = cluster.origin_lon ?? cluster.lon;
  if (lat == null || lon == null) return null;
  if (lat === 0 && lon === 0) return null;
  return { lat, lon };
}

/** Traffic-weighted center of flood hotspots that have coordinates. */
export function geoWeightedCentroid(clusters: ClusterGeoFields[]): GeoPoint | null {
  let totalWeight = 0;
  let latSum = 0;
  let lonSum = 0;

  for (const cluster of clusters) {
    const point = clusterGeoPoint(cluster);
    const weight = cluster.packet_count || 0;
    if (point == null || weight <= 0) continue;
    latSum += point.lat * weight;
    lonSum += point.lon * weight;
    totalWeight += weight;
  }

  if (totalWeight <= 0) return null;
  return { lat: latSum / totalWeight, lon: lonSum / totalWeight };
}

export function primaryClusterCoords(
  cluster: ClusterGeoFields | null,
  episode: EpisodeGeoFields,
): GeoPoint | null {
  if (cluster) {
    const fromCluster = clusterGeoPoint(cluster);
    if (fromCluster) return fromCluster;
  }
  const lat = episode.primary_origin_lat;
  const lon = episode.primary_origin_lon;
  if (lat == null || lon == null) return null;
  if (lat === 0 && lon === 0) return null;
  return { lat, lon };
}

export function resolveEpisodeLocationCoords(
  episode: EpisodeGeoFields,
  clusters: ClusterGeoFields[],
): GeoPoint | null {
  const primary = clusters[0] ?? null;
  if (primary) {
    const fromPrimary = clusterGeoPoint(primary);
    if (fromPrimary) return fromPrimary;
  }

  const centroid = geoWeightedCentroid(clusters);
  if (centroid) return centroid;

  return primaryClusterCoords(null, episode);
}

export function formatEpisodeLocationSummary(
  episode: EpisodeGeoFields,
  clusters: ClusterGeoFields[],
): string {
  const coords = resolveEpisodeLocationCoords(episode, clusters);
  if (coords) {
    return `${coords.lat.toFixed(3)}, ${coords.lon.toFixed(3)}`;
  }
  for (const cluster of clusters) {
    if (cluster.origin_geo_hint) return cluster.origin_geo_hint;
  }
  return 'Unknown';
}

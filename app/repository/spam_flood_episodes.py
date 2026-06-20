"""Persistent DM flood episode history."""

from __future__ import annotations

import json
import time
from typing import Any

from app.database import db
from app.models import SpamFloodCluster, SpamFloodEpisode

_MAX_AGE_SECONDS = 90 * 86400
_MAX_ENTRIES = 500


class SpamFloodEpisodeRepository:
    @staticmethod
    def _primary_cluster_fields(cluster: SpamFloodCluster | None) -> dict[str, Any]:
        if cluster is None:
            return {
                "primary_entry_hop": None,
                "primary_entry_name": None,
                "primary_origin_hop": None,
                "primary_origin_name": None,
                "primary_origin_lat": None,
                "primary_origin_lon": None,
                "primary_refined_route": None,
                "primary_confidence": None,
            }
        return {
            "primary_entry_hop": cluster.entry_hop,
            "primary_entry_name": cluster.entry_name,
            "primary_origin_hop": cluster.origin_hop or cluster.entry_hop,
            "primary_origin_name": cluster.origin_name or cluster.entry_name,
            "primary_origin_lat": cluster.origin_lat if cluster.origin_lat is not None else cluster.lat,
            "primary_origin_lon": cluster.origin_lon if cluster.origin_lon is not None else cluster.lon,
            "primary_refined_route": cluster.refined_route or cluster.dominant_route,
            "primary_confidence": cluster.confidence,
        }

    @staticmethod
    def _category_fields(*, category_counts: dict[str, int]) -> dict[str, Any]:
        from app.services.spam_packet_timeline import primary_category_from_counts

        return {
            "primary_category": primary_category_from_counts(category_counts),
            "category_counts_json": json.dumps(category_counts),
        }

    @staticmethod
    def _parse_category_counts(raw: str | None) -> dict[str, int]:
        if not raw:
            return {}
        parsed = json.loads(raw)
        return {str(key): int(value) for key, value in parsed.items()}

    @staticmethod
    def _parse_category_labels(raw: str | None, counts: dict[str, int]) -> dict[str, str]:
        if raw:
            parsed = json.loads(raw)
            return {str(key): str(value) for key, value in parsed.items()}
        from app.services.spam_packet_timeline import CATEGORY_LABELS

        return {key: CATEGORY_LABELS.get(key, key) for key in counts.keys()}

    @staticmethod
    def _clusters_payload(clusters: list[SpamFloodCluster]) -> str:
        return json.dumps([cluster.model_dump() for cluster in clusters])

    @staticmethod
    async def create_started(
        *,
        started_at: int,
        baseline_packets_per_window: float,
        packet_threshold: int,
        window_secs: int,
    ) -> int:
        async with db.tx() as conn:
            cursor = await conn.execute(
                """
                INSERT INTO spam_flood_episodes (
                    started_at,
                    baseline_packets_per_window,
                    packet_threshold,
                    window_secs
                ) VALUES (?, ?, ?, ?)
                """,
                (started_at, baseline_packets_per_window, packet_threshold, window_secs),
            )
            return int(cursor.lastrowid)

    @staticmethod
    async def update_progress(
        *,
        episode_id: int,
        total_packets: int,
        peak_packets_per_window: int,
        clusters: list[SpamFloodCluster],
        category_counts: dict[str, int] | None = None,
    ) -> None:
        primary = SpamFloodEpisodeRepository._primary_cluster_fields(clusters[0] if clusters else None)
        categories = SpamFloodEpisodeRepository._category_fields(
            category_counts=category_counts or {},
        )
        async with db.tx() as conn:
            await conn.execute(
                """
                UPDATE spam_flood_episodes
                SET
                    total_packets = ?,
                    peak_packets_per_window = ?,
                    primary_entry_hop = ?,
                    primary_entry_name = ?,
                    primary_origin_hop = ?,
                    primary_origin_name = ?,
                    primary_origin_lat = ?,
                    primary_origin_lon = ?,
                    primary_refined_route = ?,
                    primary_confidence = ?,
                    primary_category = ?,
                    category_counts_json = ?,
                    clusters_json = ?
                WHERE id = ?
                """,
                (
                    total_packets,
                    peak_packets_per_window,
                    primary["primary_entry_hop"],
                    primary["primary_entry_name"],
                    primary["primary_origin_hop"],
                    primary["primary_origin_name"],
                    primary["primary_origin_lat"],
                    primary["primary_origin_lon"],
                    primary["primary_refined_route"],
                    primary["primary_confidence"],
                    categories["primary_category"],
                    categories["category_counts_json"],
                    SpamFloodEpisodeRepository._clusters_payload(clusters),
                    episode_id,
                ),
            )

    @staticmethod
    async def finalize(
        *,
        episode_id: int,
        started_at: int,
        ended_at: int,
        total_packets: int,
        peak_packets_per_window: int,
        baseline_packets_per_window: float | None,
        clusters: list[SpamFloodCluster],
        category_counts: dict[str, int] | None = None,
    ) -> None:
        duration_secs = max(0, ended_at - started_at)
        anomaly_ratio = None
        if baseline_packets_per_window and baseline_packets_per_window > 0:
            anomaly_ratio = peak_packets_per_window / baseline_packets_per_window

        primary = SpamFloodEpisodeRepository._primary_cluster_fields(clusters[0] if clusters else None)
        categories = SpamFloodEpisodeRepository._category_fields(
            category_counts=category_counts or {},
        )
        async with db.tx() as conn:
            await conn.execute(
                """
                UPDATE spam_flood_episodes
                SET
                    ended_at = ?,
                    duration_secs = ?,
                    total_packets = ?,
                    peak_packets_per_window = ?,
                    baseline_packets_per_window = ?,
                    anomaly_ratio = ?,
                    primary_entry_hop = ?,
                    primary_entry_name = ?,
                    primary_origin_hop = ?,
                    primary_origin_name = ?,
                    primary_origin_lat = ?,
                    primary_origin_lon = ?,
                    primary_refined_route = ?,
                    primary_confidence = ?,
                    primary_category = ?,
                    category_counts_json = ?,
                    clusters_json = ?
                WHERE id = ?
                """,
                (
                    ended_at,
                    duration_secs,
                    total_packets,
                    peak_packets_per_window,
                    baseline_packets_per_window,
                    anomaly_ratio,
                    primary["primary_entry_hop"],
                    primary["primary_entry_name"],
                    primary["primary_origin_hop"],
                    primary["primary_origin_name"],
                    primary["primary_origin_lat"],
                    primary["primary_origin_lon"],
                    primary["primary_refined_route"],
                    primary["primary_confidence"],
                    categories["primary_category"],
                    categories["category_counts_json"],
                    SpamFloodEpisodeRepository._clusters_payload(clusters),
                    episode_id,
                ),
            )
            await SpamFloodEpisodeRepository._prune(conn)

    @staticmethod
    async def _prune(conn) -> None:
        cutoff = int(time.time()) - _MAX_AGE_SECONDS
        await conn.execute("DELETE FROM spam_flood_episodes WHERE started_at < ?", (cutoff,))
        await conn.execute(
            """
            DELETE FROM spam_flood_episodes
            WHERE id NOT IN (
                SELECT id FROM spam_flood_episodes
                ORDER BY started_at DESC
                LIMIT ?
            )
            """,
            (_MAX_ENTRIES,),
        )

    @staticmethod
    def _row_to_model(row) -> SpamFloodEpisode:
        clusters_raw = json.loads(row["clusters_json"] or "[]")
        clusters = [SpamFloodCluster.model_validate(item) for item in clusters_raw]
        category_counts = SpamFloodEpisodeRepository._parse_category_counts(
            row["category_counts_json"] if "category_counts_json" in row.keys() else None
        )
        category_labels = SpamFloodEpisodeRepository._parse_category_labels(
            row["category_labels_json"] if "category_labels_json" in row.keys() else None,
            category_counts,
        )
        return SpamFloodEpisode(
            id=row["id"],
            started_at=row["started_at"],
            ended_at=row["ended_at"],
            duration_secs=row["duration_secs"],
            total_packets=row["total_packets"],
            peak_packets_per_window=row["peak_packets_per_window"],
            baseline_packets_per_window=row["baseline_packets_per_window"],
            anomaly_ratio=row["anomaly_ratio"],
            packet_threshold=row["packet_threshold"],
            window_secs=row["window_secs"],
            primary_entry_hop=row["primary_entry_hop"],
            primary_entry_name=row["primary_entry_name"],
            primary_origin_hop=row["primary_origin_hop"],
            primary_origin_name=row["primary_origin_name"],
            primary_origin_lat=row["primary_origin_lat"],
            primary_origin_lon=row["primary_origin_lon"],
            primary_refined_route=row["primary_refined_route"],
            primary_confidence=row["primary_confidence"],
            primary_category=row["primary_category"] if "primary_category" in row.keys() else None,
            category_counts=category_counts,
            category_labels=category_labels,
            clusters=clusters,
        )

    @staticmethod
    async def close_open_episodes(*, ended_at: int | None = None) -> int:
        """Mark any in-progress episodes as ended (for example after server restart)."""
        ended = ended_at if ended_at is not None else int(time.time())
        async with db.tx() as conn:
            cursor = await conn.execute(
                """
                UPDATE spam_flood_episodes
                SET
                    ended_at = ?,
                    duration_secs = CASE WHEN ? > started_at THEN ? - started_at ELSE 0 END
                WHERE ended_at IS NULL
                """,
                (ended, ended, ended),
            )
            return int(cursor.rowcount)

    @staticmethod
    async def delete(episode_id: int) -> bool:
        async with db.tx() as conn:
            cursor = await conn.execute(
                "DELETE FROM spam_flood_episodes WHERE id = ?",
                (episode_id,),
            )
            return int(cursor.rowcount) > 0

    @staticmethod
    async def list_recent(*, limit: int = 50) -> list[SpamFloodEpisode]:
        async with db.readonly() as conn:
            async with conn.execute(
                """
                SELECT *
                FROM spam_flood_episodes
                ORDER BY started_at DESC
                LIMIT ?
                """,
                (limit,),
            ) as cursor:
                rows = await cursor.fetchall()
        return [SpamFloodEpisodeRepository._row_to_model(row) for row in rows]

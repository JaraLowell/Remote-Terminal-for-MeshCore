"""Historical packet-rate baseline for flood anomaly context."""

from __future__ import annotations

import time

from app.database import db

DEFAULT_BASELINE_LOOKBACK_DAYS = 14


class SpamBaselineService:
    @staticmethod
    async def count_packet_observations(
        *,
        since: int,
        until: int | None = None,
    ) -> int:
        """Count all stored raw packet observations in a time range."""
        until_ts = until if until is not None else int(time.time())

        async with db.readonly() as conn:
            async with conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM raw_packets
                WHERE timestamp >= ? AND timestamp < ?
                """,
                (since, until_ts),
            ) as cursor:
                row = await cursor.fetchone()

        return int(row["count"] if row else 0)

    @staticmethod
    async def count_dm_path_observations(
        *,
        since: int,
        until: int | None = None,
    ) -> int:
        """Backward-compatible alias for older tests and callers."""
        return await SpamBaselineService.count_packet_observations(
            since=since,
            until=until,
        )

    @staticmethod
    async def get_packets_per_window(
        *,
        window_secs: int,
        lookback_days: int = DEFAULT_BASELINE_LOOKBACK_DAYS,
        until: int | None = None,
    ) -> float:
        """Average packet observations per rolling window over historical data."""
        until_ts = until if until is not None else int(time.time())
        since = until_ts - lookback_days * 86400
        if since >= until_ts:
            return 0.0

        total = await SpamBaselineService.count_packet_observations(since=since, until=until_ts)
        elapsed_secs = until_ts - since
        return (total / elapsed_secs) * window_secs

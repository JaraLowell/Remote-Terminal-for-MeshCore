import logging
import time

from app.database import db
from app.models import LocationHistory

logger = logging.getLogger(__name__)


class LocationHistoryRepository:
    @staticmethod
    async def record(
        contact_public_key: str,
        lat: float,
        lon: float,
        timestamp: int,
        altitude: int | None = None,
        speed: float | None = None,
        heading: float | None = None,
        satellites: int | None = None,
        battery: int | None = None,
    ) -> int:
        """
        Insert a location history entry only if the position has changed.
        Returns the inserted row ID, or 0 if skipped due to duplicate position.
        """
        received_at = int(time.time())
        async with db.tx() as conn:
            # Check if the last logged position matches (within 0.000001 degrees ~= 0.1m)
            async with conn.execute(
                """
                SELECT lat, lon FROM contact_location_history
                WHERE contact_public_key = ?
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (contact_public_key,),
            ) as cursor:
                last_row = await cursor.fetchone()

            if last_row:
                last_lat, last_lon = last_row["lat"], last_row["lon"]
                # Skip if position hasn't changed (tolerance: 0.000001 degrees)
                if abs(lat - last_lat) < 0.000001 and abs(lon - last_lon) < 0.000001:
                    logger.debug(
                        "Skipping duplicate position for %s (lat=%.6f, lon=%.6f)",
                        contact_public_key[:12],
                        lat,
                        lon,
                    )
                    return 0

            async with conn.execute(
                """
                INSERT INTO contact_location_history
                    (contact_public_key, lat, lon, altitude, speed, heading, 
                     satellites, battery, timestamp, received_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    contact_public_key,
                    lat,
                    lon,
                    altitude,
                    speed,
                    heading,
                    satellites,
                    battery,
                    timestamp,
                    received_at,
                ),
            ) as cursor:
                return cursor.lastrowid or 0

    @staticmethod
    async def get_history(
        contact_public_key: str, since_timestamp: int | None = None
    ) -> list[LocationHistory]:
        """
        Return location history for a contact, optionally filtered by timestamp.
        Ordered by timestamp ASC (oldest first).
        """
        async with db.readonly() as conn:
            if since_timestamp is not None:
                async with conn.execute(
                    """
                    SELECT id, contact_public_key, lat, lon, altitude, speed, heading,
                           satellites, battery, timestamp, received_at
                    FROM contact_location_history
                    WHERE contact_public_key = ? AND timestamp >= ?
                    ORDER BY timestamp ASC
                    """,
                    (contact_public_key, since_timestamp),
                ) as cursor:
                    rows = await cursor.fetchall()
            else:
                async with conn.execute(
                    """
                    SELECT id, contact_public_key, lat, lon, altitude, speed, heading,
                           satellites, battery, timestamp, received_at
                    FROM contact_location_history
                    WHERE contact_public_key = ?
                    ORDER BY timestamp ASC
                    """,
                    (contact_public_key,),
                ) as cursor:
                    rows = await cursor.fetchall()

        return [
            LocationHistory(
                id=row["id"],
                contact_public_key=row["contact_public_key"],
                lat=row["lat"],
                lon=row["lon"],
                altitude=row["altitude"],
                speed=row["speed"],
                heading=row["heading"],
                satellites=row["satellites"],
                battery=row["battery"],
                timestamp=row["timestamp"],
                received_at=row["received_at"],
            )
            for row in rows
        ]

    @staticmethod
    async def get_all_recent(retention_hours: int) -> dict[str, list[LocationHistory]]:
        """
        Return location history for all trackers within the retention window.
        Returns a dict mapping contact public_key -> list of LocationHistory.
        """
        cutoff = int(time.time()) - (retention_hours * 3600)
        async with db.readonly() as conn:
            async with conn.execute(
                """
                SELECT id, contact_public_key, lat, lon, altitude, speed, heading,
                       satellites, battery, timestamp, received_at
                FROM contact_location_history
                WHERE received_at >= ?
                ORDER BY contact_public_key, timestamp ASC
                """,
                (cutoff,),
            ) as cursor:
                rows = await cursor.fetchall()

        result: dict[str, list[LocationHistory]] = {}
        for row in rows:
            entry = LocationHistory(
                id=row["id"],
                contact_public_key=row["contact_public_key"],
                lat=row["lat"],
                lon=row["lon"],
                altitude=row["altitude"],
                speed=row["speed"],
                heading=row["heading"],
                satellites=row["satellites"],
                battery=row["battery"],
                timestamp=row["timestamp"],
                received_at=row["received_at"],
            )
            key = row["contact_public_key"]
            if key not in result:
                result[key] = []
            result[key].append(entry)

        return result

    @staticmethod
    async def prune_old_entries(retention_hours: int) -> int:
        """
        Delete location history entries older than retention_hours.
        Returns count of deleted rows.
        """
        cutoff = int(time.time()) - (retention_hours * 3600)
        async with db.tx() as conn:
            async with conn.execute(
                "DELETE FROM contact_location_history WHERE received_at < ?",
                (cutoff,),
            ) as cursor:
                return cursor.rowcount or 0

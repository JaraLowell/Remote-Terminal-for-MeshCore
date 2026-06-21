import logging

import aiosqlite

logger = logging.getLogger(__name__)


async def migrate(conn: aiosqlite.Connection) -> None:
    """Persist likely spam source identity on flood episodes."""
    cursor = await conn.execute("PRAGMA table_info(spam_flood_episodes)")
    columns = {row[1] for row in await cursor.fetchall()}

    additions = {
        "likely_source_key": "TEXT",
        "likely_source_label": "TEXT",
        "likely_source_name": "TEXT",
        "likely_source_public_key": "TEXT",
        "likely_source_lat": "REAL",
        "likely_source_lon": "REAL",
        "likely_source_geo_hint": "TEXT",
        "likely_source_traffic_share": "REAL",
        "likely_source_packet_count": "INTEGER",
        "likely_source_kind": "TEXT",
    }

    for column, column_type in additions.items():
        if column not in columns:
            await conn.execute(
                f"ALTER TABLE spam_flood_episodes ADD COLUMN {column} {column_type}"
            )

    await conn.commit()

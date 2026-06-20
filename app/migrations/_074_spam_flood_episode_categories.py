import logging

import aiosqlite

logger = logging.getLogger(__name__)


async def migrate(conn: aiosqlite.Connection) -> None:
    """Store dominant packet category and per-type counts on flood episodes."""
    cursor = await conn.execute("PRAGMA table_info(spam_flood_episodes)")
    columns = {row[1] for row in await cursor.fetchall()}

    if "primary_category" not in columns:
        await conn.execute(
            "ALTER TABLE spam_flood_episodes ADD COLUMN primary_category TEXT"
        )

    if "category_counts_json" not in columns:
        await conn.execute(
            """
            ALTER TABLE spam_flood_episodes
            ADD COLUMN category_counts_json TEXT NOT NULL DEFAULT '{}'
            """
        )

    await conn.commit()

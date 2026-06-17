import logging

import aiosqlite

logger = logging.getLogger(__name__)


async def migrate(conn: aiosqlite.Connection) -> None:
    """Persist last-known tracker heading on contacts for map display."""
    await conn.execute(
        """
        ALTER TABLE contacts ADD COLUMN tracker_heading REAL
        """
    )
    logger.debug("Added contacts.tracker_heading column")

import logging

import aiosqlite

logger = logging.getLogger(__name__)


async def migrate(conn: aiosqlite.Connection) -> None:
    """
    Add tracker location history support:
    1. Create contact_location_history table for storing tracker position updates
    2. Add tracker_history_hours setting (default 12 hours)
    3. Add is_tracker and tracker_name columns to contacts

    The location history table stores timestamped lat/lon positions for contacts
    that send LOCATION packets (0x0D). Old entries are auto-pruned based on the
    tracker_history_hours setting.
    """
    # Create location history table
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS contact_location_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_public_key TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            altitude INTEGER,
            speed REAL,
            heading REAL,
            satellites INTEGER,
            battery INTEGER,
            timestamp INTEGER NOT NULL,
            received_at INTEGER NOT NULL,
            FOREIGN KEY (contact_public_key) REFERENCES contacts(public_key) ON DELETE CASCADE
        )
        """
    )

    # Index for efficient history queries and pruning
    await conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_location_history_contact_time
        ON contact_location_history(contact_public_key, timestamp DESC)
        """
    )

    # Index for efficient cleanup of old entries
    await conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_location_history_received_at
        ON contact_location_history(received_at)
        """
    )

    # Add tracker fields to contacts table
    await conn.execute(
        """
        ALTER TABLE contacts ADD COLUMN is_tracker INTEGER DEFAULT 0
        """
    )

    await conn.execute(
        """
        ALTER TABLE contacts ADD COLUMN tracker_name TEXT
        """
    )

    # Add tracker history retention setting (hours)
    await conn.execute(
        """
        ALTER TABLE app_settings ADD COLUMN tracker_history_hours INTEGER DEFAULT 12
        """
    )

    await conn.commit()
    logger.debug("Created contact_location_history table and added tracker columns")

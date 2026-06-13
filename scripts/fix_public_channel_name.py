#!/usr/bin/env python3
"""Fix existing Public channel name to canonical 'Public' capitalization."""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Database
from app.config import settings
from app.channel_constants import PUBLIC_CHANNEL_KEY, PUBLIC_CHANNEL_NAME


async def main():
    db = Database(settings.database_path)
    await db.connect()
    
    print(f"Fixing Public channel name to canonical '{PUBLIC_CHANNEL_NAME}'...\n")
    
    # Check current state
    async with db.readonly() as conn:
        async with conn.execute(
            "SELECT name FROM channels WHERE key = ?",
            (PUBLIC_CHANNEL_KEY,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                print(f"✗ Public channel (key {PUBLIC_CHANNEL_KEY}) not found in database")
                await db.disconnect()
                return
            
            current_name = row['name']
            print(f"Current name: '{current_name}'")
    
    if current_name == PUBLIC_CHANNEL_NAME:
        print(f"✓ Already correct! No changes needed.")
    else:
        # Update to canonical name
        async with db.tx() as conn:
            await conn.execute(
                "UPDATE channels SET name = ? WHERE key = ?",
                (PUBLIC_CHANNEL_NAME, PUBLIC_CHANNEL_KEY)
            )
        
        print(f"✓ Updated to: '{PUBLIC_CHANNEL_NAME}'")
        print("\nDone! The Public channel name has been normalized.")
    
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

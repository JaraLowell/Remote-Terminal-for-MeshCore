#!/usr/bin/env python3
"""Check for multiple Public-like channels in the database."""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Database
from app.config import settings


async def main():
    db = Database(settings.database_path)
    await db.connect()
    
    public_variants = [
        ("Public (canonical)", "8B3387E9C5CDEA6AC9E5EDBAA115CD72"),
        ("#public (hashtag)", "8B4B705B080C0D943B1C80F6B3EF6B6D"),
        ("#Public (hashtag)", "7534FE292203CCDCE93DB79377D4B566"),
    ]
    
    print("Checking for Public-like channels in database...\n")
    
    found_channels = []
    async with db.readonly() as conn:
        for name, key in public_variants:
            async with conn.execute(
                "SELECT key, name, is_hashtag FROM channels WHERE key = ?",
                (key,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    found_channels.append((name, key, row))
                    print(f"✓ FOUND: {name}")
                    print(f"  Key:  {row['key']}")
                    print(f"  Name: {row['name']}")
                    print(f"  Hashtag: {bool(row['is_hashtag'])}")
                    print()
    
    if not found_channels:
        print("No Public-like channels found in database.")
    else:
        print(f"\nTotal: {len(found_channels)} Public-like channel(s) found")
        
        # Count messages for each
        print("\nMessage counts:")
        async with db.readonly() as conn:
            for name, key, row in found_channels:
                async with conn.execute(
                    "SELECT COUNT(*) as count FROM messages WHERE conversation_key = ? AND type = 'CHAN'",
                    (key,)
                ) as cursor:
                    msg_row = await cursor.fetchone()
                    count = msg_row["count"] if msg_row else 0
                    print(f"  {name}: {count} messages")
    
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

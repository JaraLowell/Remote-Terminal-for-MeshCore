"""Check which database file we're actually reading."""
import asyncio

async def check_db_info():
    from app.config import settings
    from app.database import db
    from app.repository.contacts import ContactRepository
    
    print(f"Database path from settings: {settings.database_path}")
    print(f"Database object path: {db.db_path}")
    
    if db._connection is None:
        await db.connect()
    
    contacts = await ContactRepository.get_all()
    print(f"\nTotal contacts in database: {len(contacts)}")
    
    # Search for the specific contact
    target_key = "109da48ca8fb1ff1fa2dd1348e365fb63ad82cad0552d8831caa9bf7625ba75e"
    
    print(f"\nSearching for contact: {target_key[:16]}...")
    
    for c in contacts:
        if c.public_key.lower() == target_key.lower():
            print(f"\n✅ FOUND IT!")
            print(f"   Name: {c.name or '(no name)'}")
            print(f"   Public Key: {c.public_key}")
            print(f"   Location: {c.lat}, {c.lon}")
            print(f"   Last Seen: {c.last_seen}")
            print(f"   On Radio: {bool(c.on_radio)}")
            return
    
    # Try case-insensitive prefix match
    for c in contacts:
        if c.public_key.lower().startswith("109da48c"):
            print(f"\n✅ Found contact starting with 109da48c:")
            print(f"   Name: {c.name or '(no name)'}")
            print(f"   Public Key: {c.public_key}")
            print(f"   Location: {c.lat}, {c.lon}")
            return
    
    print(f"\n❌ Contact NOT found in database")
    print(f"\nPossible reasons:")
    print(f"1. Contact was added while server is running (requires restart or sync)")
    print(f"2. Different database file (check if server uses a different data/ directory)")
    print(f"3. Contact add failed silently")
    
    # Show a few example contacts to verify we're reading the right DB
    print(f"\nShowing first 5 contacts to verify correct database:")
    for c in contacts[:5]:
        print(f"   {c.public_key[:16]}... - {c.name or '(no name)'}")

if __name__ == "__main__":
    asyncio.run(check_db_info())

"""Search for contact with flexible matching."""
import asyncio

async def flexible_search():
    from app.database import db
    from app.repository.contacts import ContactRepository
    
    if db._connection is None:
        await db.connect()
    
    contacts = await ContactRepository.get_all()
    print(f"Total contacts: {len(contacts)}\n")
    
    # Search for any contact with "109d" in the key (very loose match)
    target_prefix = "109d"
    
    print(f"Searching for contacts with '{target_prefix}' anywhere in public key...\n")
    
    matches = []
    for c in contacts:
        if target_prefix.lower() in c.public_key.lower():
            matches.append(c)
            print(f"✅ MATCH:")
            print(f"   Name: {c.name or '(no name)'}")
            print(f"   Public Key (first 20): {c.public_key[:20]}...")
            print(f"   Public Key (full): {c.public_key}")
            print(f"   Location: {c.lat}, {c.lon}")
            print(f"   Last Seen: {c.last_seen}")
            print(f"   On Radio: {bool(c.on_radio)}")
            
            # Check exact prefix match
            if c.public_key.lower().startswith("109da48c"):
                print(f"   ✅ This key DOES start with '109da48c'")
            else:
                print(f"   ❌ Key does NOT start with '109da48c' (starts with: {c.public_key[:8].lower()})")
            print()
    
    if not matches:
        print(f"❌ No contacts found with '{target_prefix}' in the key")
        print(f"\nLet's check contacts that have GPS coordinates set:")
        for c in contacts:
            if c.lat and c.lon and c.lat != 0.0 and c.lon != 0.0:
                # Check if near the tracker location (52.7, 5.2)
                if 52.5 < c.lat < 52.9 and 5.0 < c.lon < 5.5:
                    print(f"\n   {c.public_key[:16]}... - {c.name or '(no name)'}")
                    print(f"   Location: {c.lat}, {c.lon}")
                    print(f"   First 8 chars: {c.public_key[:8]}")
    
    print(f"\n\nFound {len(matches)} match(es)")

if __name__ == "__main__":
    asyncio.run(flexible_search())

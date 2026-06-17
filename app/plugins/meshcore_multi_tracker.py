"""
RemoteTerm handles incoming packets via a centralized router loop, typically found in a file like app/main.py or app/core/router.py.
You need to import your class and inject it into the packet stream handler [jkingsman/Remote-Terminal-for-MeshCore].

Open the main application packet handler file and add these entries:
  At the top of the file (with the imports):
    from app.plugins.meshcore_multi_tracker import RemoteTermMultiTracker

  Inside the initialization section (where the application state starts up):
    # Initialize the tracking engine instance
    global anti_spam_tracker
    anti_spam_tracker = RemoteTermMultiTracker()

  Inside the on_packet_received or process_incoming_packet function:Find the exact function where RemoteTerm decodes raw serial JSON frames into a Python dictionary.
  Right after the packet is decrypted and stored, pipe it directly into your bot:
    # Pass the processed packet dictionary to your spatial tracking bot
    try:
        anti_spam_tracker.on_packet(packet)
    except Exception as e:
        logger.error(f"Anti-spam plugin exception: {e}")
"""
import os
import time
import sqlite3
from collections import deque, Counter

# 1. LIVE INFRASTRUCTURE FILTER KEYS OF KNOWN MQTT LINKED GATEWAYS
KNOWN_GATEWAYS = {
    "1228d131fa4b13c78a7aefee124e5c7fe51a8555115220d64d1df749b5a7de8c", # Bridge Sf7 Gwnl Ledeacker
    "753c3a558d71c52669cf59d67dd9be41725efd8af113b2f2f36925bde002f5b1", # Bridge Sf8 Gwnl Ledeacker
    "db371c0634d23dd4dc72556366f6cd19578ac91eb85257ea259af8f8bb1d14e0", # NL-GR Bridge Mussel
    "40b8bacb92538bdaa3d45abb759dd8cfcefaefc5a8f1e77d0f3dc6b7b5452429", # StedeBroec-Bridge
    "82e422e3a9d279d31df8794439dd92803db0658c9d6579cc717bbc0f266070dd", # TB sf7 gwnl Passion Vhz
    "2092ae5d57ff8836f2047a1f74f695084247aac2b85cdc5d4ecf7cb9f2ad3c0e", # TCP Bridge-gwnl-mobile
    "8fb483861e77a9e8021ed546510ba6deb9e7708dd2330c407f05e085a8f6e31a", # 📶RPT Aurich 1 GWNL
    "d26506b1ed9c8a839bfca3b1ab0afe64a6e30fb47cb0d742d2f81efbee2a17e2", # 📶RPT Norden 2 GWNL
    "7d5abd286e07f4995dda8a220d044ef2f13949fcc4f3621e4a69bfc20519259a", # 📶RPT Norden GWNL 🇳🇱
    "eb46b319cd2dac975ae178d07d57806fd6b8a4d5301027d76fbd3b3f8df3e3f8", # 📶RPT#GWNLHoofddorp
    "66cca85f210d7af515f8c5760aa222ba1072762446b7fddaef36308a3a12513b", # 📶RPTsf7 MOB 2 GWNL👀
    "049314d147f018f44633be5b8a4852279295bb5eced77488c451ec83ebc28afa"  # 📶RPTsf8 MOB 1 GWNL👀
}

# Configured to look at a rolling window of the last 30 seconds to catch overlapping streams
ATTACK_WINDOW_SECS = 30
ATTACK_PACKET_COUNT = 50 

packet_history = deque()

class RemoteTermMultiTracker:
    def __init__(self, context=None):
        self.context = context
        self.db_path = os.path.join("data", "meshcore.db")
        print("🤖 Multi-Target Spatial Clustering Plugin Activated.")

    def fetch_contact_geo(self, hop_bytes):
        """Queries the contacts table looking strictly for prefix matches."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name, lat, lon FROM contacts WHERE public_key = ? OR public_key LIKE ? LIMIT 1", 
                (hop_bytes, f"{hop_bytes}%")
            )
            row = cursor.fetchone()
            conn.close()
            if row and row['lat'] and row['lon'] and float(row['lat']) != 0.0:
                return {"name": row['name'], "lat": float(row['lat']), "lon": float(row['lon'])}
        except Exception as e:
            print(f"⚠️ Query error: {e}")
        return None

    def on_packet(self, packet):
        current_time = time.time()
        packet_type = packet.get("type") or packet.get("packet_type")
        source_id = str(packet.get("from") or packet.get("source_id", "")).upper()
        
        raw_path = packet.get("hop_history") or packet.get("path") or []
        clean_path = [str(h).lower().strip() for h in raw_path]

        # Filter for randomized short-ID attacks
        if packet_type == "DM" and len(source_id) <= 4:
            # Reconstruct pure RF hops before it reached an internet gateway
            rf_only_path = []
            for hop in clean_path:
                if hop in KNOWN_GATEWAYS:
                    break
                rf_only_path.append(hop)
            
            if rf_only_path:
                packet_history.append({
                    "timestamp": current_time,
                    "entry_node": rf_only_path[0], # The very first physical over-the-air ear
                    "full_rf_path": tuple(rf_only_path)
                })

        while packet_history and (current_time - packet_history[0]["timestamp"] > ATTACK_WINDOW_SECS):
            packet_history.popleft()

        if len(packet_history) >= ATTACK_PACKET_COUNT:
            self.process_multi_cluster_analysis()

    def process_multi_cluster_analysis(self):
        """
        Groups traffic dynamically by physical entry vectors.
        Isolates multiple simultaneous attackers completely independently.
        """
        # Group packets by the first physical node that heard them
        clusters = {}
        for p in packet_history:
            entry = p["entry_node"]
            if entry not in clusters:
                clusters[entry] = []
            clusters[entry].append(p)

        print(f"\n🚨 [CRITICAL: COORDINATED MULTI-FLOOD DETECTED]")
        print(f" Total Active Volume: {len(packet_history)} packets in progress across network.")
        print("==================================================================")

        attacker_index = 1
        for entry_node, packets in clusters.items():
            # Only track a cluster if it contributes significant volume (e.g., > 15% of the total spam)
            if len(packets) < (ATTACK_PACKET_COUNT * 0.15):
                continue
                
            # Collect path variations within this specific cluster
            path_blueprints = Counter([p["full_rf_path"] for p in packets]).most_common(1)
            dominant_path = " ──► ".join(path_blueprints[0][0]) if path_blueprints else entry_node
            
            # Fetch GPS data for this specific cluster's entry point
            geo = self.fetch_contact_geo(entry_node)
            
            print(f"🔥 ATTACK HOTSPOT #{attacker_index} ")
            print(f" 📦 Active Path Footprint: [ {dominant_path} ]")
            print(f" 📊 Burst Volume          : {len(packets)} packets captured")
            
            if geo:
                print(f" 📶 Primary Entry Node    : {geo['name']} (Key prefix: {entry_node})")
                print(f" 🎯 Pinpointed Coordinates: Lat {geo['lat']:.5f}, Lon {geo['lon']:.5f}")
                print(f" 🗺️  Target Field Map Link : https://google.com{geo['lat']},{geo['lon']}")
            else:
                print(f" 📶 Primary Entry Node    : [0x{entry_node}] (No coordinate tracking data inside contacts table)")
            print("------------------------------------------------------------------")
            attacker_index += 1
        print("==================================================================\n")

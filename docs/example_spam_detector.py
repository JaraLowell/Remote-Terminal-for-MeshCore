# Spam Detection Bot
# Tracks message frequency per sender and alerts on suspicious activity
#
# To use this bot:
# 1. Go to Settings > Fanout in the RemoteTerm web interface
# 2. Create a new Bot fanout config
# 3. Paste this entire code
# 4. Configure the scope to listen to specific channels or all messages
# 5. Set the alert channel where spam warnings should be sent
# 6. Enable the bot

import time

# Global state - persists across bot invocations within the same bot instance
message_history = {}  # {sender_key: [timestamp1, timestamp2, ...]}
spam_alerts_sent = {}  # {sender_key: last_alert_timestamp} to avoid alerting repeatedly
no_advert_warnings = {}  # {sender_key: last_warning_timestamp} for nodes without adverts

# Configuration
SPAM_THRESHOLD = 30  # Number of messages to trigger spam alert
TIME_WINDOW = 3600  # Time window in seconds (1 hour)
ALERT_COOLDOWN = 3600  # Minimum seconds between alerts for the same sender (1 hour)
NO_ADVERT_THRESHOLD = 10  # Message count to warn about missing advertisements
NO_ADVERT_COOLDOWN = 7200  # Cooldown for no-advert warnings (2 hours)

# Alert routing configuration
# Set to a channel key (32 hex chars) to send all alerts to a specific channel
# Leave as None or empty string to send alerts back to the channel where spam was detected
# Example: ALERT_CHANNEL_KEY = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
ALERT_CHANNEL_KEY = "f27acf0bf185c2ec4b9fd36bf12fa1ee"  # Set this to your admin/alert channel key

def bot(sender_name, sender_key, message_text, is_dm, channel_key, channel_name, 
        sender_timestamp, received_at, path, is_outgoing=False, path_bytes_per_hop=None, 
        packet_hash=None, region_name=None, **kwargs):
    """
    Detects potential spam by tracking message frequency per sender.
    
    Alerts when:
    - A sender exceeds SPAM_THRESHOLD messages in TIME_WINDOW seconds
    - A sender with no advertisement path sends multiple messages (possible spoofing)
    
    If ALERT_CHANNEL_KEY is configured, alerts are sent to that channel.
    Otherwise, alerts are sent to the same channel where spam was detected.
    """
    
    # Ignore our own outgoing messages to prevent self-tracking
    if is_outgoing:
        return None
    
    # Only track messages with a sender_key (identified senders)
    if not sender_key:
        return None
    
    # Use received_at for accurate timing, fall back to current time
    current_time = received_at if received_at else int(time.time())
    
    # Initialize tracking for this sender if needed
    if sender_key not in message_history:
        message_history[sender_key] = []
    
    # Add current message timestamp
    message_history[sender_key].append(current_time)
    
    # Clean up old messages outside the time window
    cutoff_time = current_time - TIME_WINDOW
    message_history[sender_key] = [
        ts for ts in message_history[sender_key] 
        if ts > cutoff_time
    ]
    
    # Get current message count in the time window
    message_count = len(message_history[sender_key])
    
    # Format sender info for alerts
    sender_info = sender_name if sender_name else f"Node {sender_key[:12]}"
    location_info = ""
    
    # Check for missing advertisement path (possible spoofing)
    has_path = path and isinstance(path, str) and path not in ("", "0")
    
    if not has_path and message_count >= NO_ADVERT_THRESHOLD:
        # This sender has no path but is sending messages - suspicious
        last_warning = no_advert_warnings.get(sender_key, 0)
        
        if current_time - last_warning > NO_ADVERT_COOLDOWN:
            no_advert_warnings[sender_key] = current_time
            location_info = " ⚠️ No advertisement path seen - possible identity spoofing"
    
    alert_message = None
    
    # Check if this sender has exceeded the spam threshold
    if message_count > SPAM_THRESHOLD:
        # Check if we've already alerted about this sender recently
        last_alert = spam_alerts_sent.get(sender_key, 0)
        
        if current_time - last_alert > ALERT_COOLDOWN:
            # Update alert timestamp
            spam_alerts_sent[sender_key] = current_time
            
            # Build alert message
            alert_message = f"🚨 SPAM ALERT: {sender_info} sent {message_count} messages in last hour"
            
            # Add path information
            if has_path:
                if path_bytes_per_hop:
                    path_bytes = len(path) // 2
                    hop_count = path_bytes // path_bytes_per_hop
                    alert_message += f" (via {hop_count} hop{'s' if hop_count != 1 else ''})"
                else:
                    alert_message += f" (path: {path[:16]}...)"
            else:
                alert_message += " - NO PATH/ADVERT SEEN"
            
            # Add location info if available
            alert_message += location_info
            
            # Add channel context if applicable
            if not is_dm and channel_name:
                alert_message += f" in {channel_name}"
            
            # Suggest actions
            if not has_path:
                alert_message += " | Suggest: Check if this node exists or block sender"
    
    # Check for suspicious activity without full spam threshold
    elif message_count >= SPAM_THRESHOLD * 0.75 and not has_path:
        # 75% of threshold + no path = very suspicious
        last_alert = spam_alerts_sent.get(sender_key + "_warning", 0)
        
        if current_time - last_alert > ALERT_COOLDOWN:
            spam_alerts_sent[sender_key + "_warning"] = current_time
            
            alert_message = f"⚠️ Suspicious activity: {sender_info} sent {message_count} messages "
            alert_message += f"without advertisement path | Key: {sender_key[:12]}"
            
            if not is_dm and channel_name:
                alert_message += f" in {channel_name}"
    
    # Send alert if one was generated
    if alert_message:
        # If ALERT_CHANNEL_KEY is configured, send to that channel
        if ALERT_CHANNEL_KEY:
            _send_to_alert_channel(alert_message)
            return None  # Don't also send to original channel
        else:
            # Return normally - will send to original channel/DM
            return alert_message
    
    # No spam detected or already alerted recently
    return None


def _send_to_alert_channel(message):
    """
    Helper to send a message to the configured alert channel.
    This runs synchronously but the bot system handles it in an executor.
    """
    import asyncio
    
    # Import the message sending functions from the app
    try:
        from app.models import SendChannelMessageRequest
        from app.routers.messages import send_channel_message
        
        # Create the request
        request = SendChannelMessageRequest(
            channel_key=ALERT_CHANNEL_KEY,
            text=message
        )
        
        # We're in a sync context (bot code runs in thread pool)
        # We need to run the async function
        try:
            # Try to get the running event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create a new task in the running loop
                asyncio.run_coroutine_threadsafe(send_channel_message(request), loop)
            else:
                # No running loop, run directly
                asyncio.run(send_channel_message(request))
        except RuntimeError:
            # No event loop, create one
            asyncio.run(send_channel_message(request))
            
    except ImportError as e:
        # If imports fail, log it (though logger may not be available in bot context)
        print(f"Failed to import message sending functions: {e}")
    except Exception as e:
        print(f"Failed to send alert to channel: {e}")


# USAGE NOTES:
# ============
# 
# 1. SCOPE CONFIGURATION:
#    - Set scope to "all" to monitor all channels and DMs
#    - Or set to specific channels like "#general" to monitor just those
#    - When using ALERT_CHANNEL_KEY, scope should be "all" or cover the channels you want to monitor
#
# 2. ALERT ROUTING (NEW!):
#    - Set ALERT_CHANNEL_KEY to route all spam alerts to a specific admin/alert channel
#    - To find your channel key: In RemoteTerm, go to the channel, check the URL or use Settings
#    - Example: ALERT_CHANNEL_KEY = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
#    - Leave as None to send alerts to the same channel where spam was detected (default)
#    - With ALERT_CHANNEL_KEY set, alerts include which channel the spam came from
#
# 3. HOW TO GET YOUR CHANNEL KEY:
#    - Open RemoteTerm web interface
#    - Navigate to your admin/alert channel
#    - Look in the browser URL: /chat/channel/{channel_key}
#    - Copy the 32-character hex string
#    - Paste into ALERT_CHANNEL_KEY = "your_key_here"
#
# 4. TUNING THRESHOLDS:
#    - SPAM_THRESHOLD: Adjust based on your network's normal activity (default: 30)
#    - TIME_WINDOW: 3600 = 1 hour, increase for less sensitive detection
#    - NO_ADVERT_THRESHOLD: Lower number = more sensitive to spoofing attempts
#
# 5. PATH DISCOVERY:
#    - The bot alerts when no advertisement path is seen
#    - You can manually trigger path discovery for suspicious nodes via:
#      Contact pane > [node] > "Trace" or "Path Discovery" buttons
#    - This helps identify if the node is real or spoofed
#
# 6. BLOCKING SPAMMERS:
#    - Go to Settings > Blocked Keys to block the sender's public key
#    - Or Settings > Blocked Names to block by display name
#
# 7. FALSE POSITIVES:
#    - Legitimate bots or automated systems may trigger alerts
#    - Consider whitelisting known bots by checking sender_key and returning None
#    - Example: Add at the top of bot(): if sender_key == "known_bot_key": return None
#
# 8. MEMORY USAGE:
#    - The bot maintains message history in memory
#    - Old entries are automatically cleaned up after TIME_WINDOW
#    - For very high-traffic networks, consider increasing ALERT_COOLDOWN
#
# EXAMPLE SETUP WITH DEDICATED ALERT CHANNEL:
# ===========================================
# 1. Create a channel for alerts (e.g., #spam-alerts)
# 2. Get the channel key from the URL when viewing that channel
# 3. Set ALERT_CHANNEL_KEY = "paste_your_32_char_key_here"
# 4. Set bot scope to "all" to monitor all messages
# 5. Enable the bot
# 6. All spam alerts will now appear in #spam-alerts instead of the spam channel

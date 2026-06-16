# LOCATION Packet Byte Order Fix

## Problem

Your real LOCATION packet (0x0D) from "NL2JVV GPS Tracker" was parsing with incorrect values:
- ❌ Altitude: 1280m (expected: 5m)
- ❌ Battery: 40974mV (expected: 3744mV)
- ❌ Timestamp: Year 2050 (expected: June 2026)

## Root Cause

The LOCATION packet format uses **big-endian (network byte order)** for ALL multi-byte fields, but our initial implementation incorrectly used little-endian.

## Fix Applied

Updated `app/decoder.py` to use big-endian for all multi-byte fields:
- ✅ Latitude/Longitude: Now using `"big"` instead of `"little"`
- ✅ Altitude: Now using `"big"` instead of `"little"`
- ✅ Speed: Now using `"big"` instead of `"little"`
- ✅ Heading: Now using `"big"` instead of `"little"`
- ✅ Battery: Now using `"big"` instead of `"little"`
- ✅ Timestamp: Now using `"big"` instead of `"little"`

Updated all tests in `tests/test_location_packet.py` to generate correct test data with big-endian encoding.

## Verified Working

Your real packet now decodes correctly:

```
📍 NL2JVV GPS Tracker: 52.700917, 5.228158 (alt: 5m, speed: 0.0m/s, hdg: 0.0°, sats: 12, batt: 3744mV)
```

Location: **Harderwijk, Netherlands** (52.7°N, 5.2°E)

## Test Results

- ✅ 10/10 location packet tests pass
- ✅ 62/62 packet pipeline tests pass
- ✅ 4/4 frontend location display tests pass
- ✅ No TypeScript errors

## What You'll See

When you receive a LOCATION packet (0x0D), the Raw Packet Feed will display:

**Summary**: "Location from NL2JVV GPS Tracker via {path}"
**Decoded Message** (green box):
```
📍 NL2JVV GPS Tracker: 52.700917, 5.228158 (alt: 5m, speed: 0.0m/s, hdg: 0.0°, sats: 12, batt: 3744mV)
```

## Next Steps

1. Rebuild frontend: `cd frontend && npm run build`
2. Restart server
3. Verify LOCATION packets display correctly in Raw Packet Feed

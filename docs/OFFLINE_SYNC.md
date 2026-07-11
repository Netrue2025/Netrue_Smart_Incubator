# Offline Sync Flow

```text
Normal operation
ESP32 reads DHT22 -> controls relay -> stores reading -> POST /api/environment

WiFi/backend unavailable
ESP32 reads DHT22 -> controls relay -> appends reading to SPIFFS queue

Connectivity returns
ESP32 reconnects -> downloads latest settings -> replays queued readings oldest first

Settings conflict
Backend compares timestamps and keeps the newest settings payload
```

Relay control does not depend on the backend. Emergency OFF, sensor failures, and relay timeout always force the heater OFF locally.

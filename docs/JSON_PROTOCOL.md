# JSON Protocol

## Telemetry From ESP32

```json
{
  "temperature": 37.4,
  "humidity": 61.2,
  "heat_index": 38.1,
  "relay": true,
  "fan_relay": true,
  "wifi": true,
  "sync_status": "synced",
  "timestamp": "2026-06-30T12:00:00Z"
}
```

## Commands To ESP32

The firmware downloads `/api/settings` and applies newer settings by timestamp.

```json
{
  "target_temperature": 37.5,
  "target_humidity": 60,
  "tolerance": 0.3,
  "hysteresis": 0.2,
  "relay_mode": "AUTO",
  "manual_relay": false,
  "emergency_off": false,
  "tray_servo_enabled": true,
  "tray_servo_angle": 45,
  "tray_servo_interval_minutes": 120,
  "tray_servo_speed_dps": 6,
  "updated_at": "2026-06-30T12:00:00Z"
}
```

## Relay Command

```json
{
  "mode": "MANUAL",
  "relay": true,
  "reason": "operator command"
}
```

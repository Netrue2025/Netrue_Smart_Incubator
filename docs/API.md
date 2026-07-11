# API Documentation

Base URL: `http://localhost:8000/api`

## Status

`GET /status`

Returns backend status, latest environment reading, settings, device online state, database count, and queue size.

## Environment

`GET /environment`

Returns the latest sensor reading.

`POST /environment`

Accepts firmware telemetry:

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

## History

`GET /history?range=today|week|month|custom`

For custom range, pass `start` and `end` ISO timestamps.

## Settings

`GET /settings`

`POST /settings`

Validated fields include target temperature, target humidity, tolerance, hysteresis, relay mode, tray servo settings, sampling interval, sync interval, calibration offsets, device name, and timezone. Firmware telemetry also reports `fan_relay` for the GPIO23 fan relay state.

Firmware should call `GET /settings?firmware=true` so pending WiFi credentials
are included for device provisioning. Normal dashboard reads do not include the
saved WiFi password.

## WiFi Provisioning

- `POST /wifi/scan` queues an ESP32 WiFi scan.
- `GET /wifi/networks` returns the latest SSIDs reported by the ESP32.
- `POST /wifi/connect` stores the target SSID/password and queues a reconnect.
- `POST /wifi/networks` is used by firmware to upload scan results.
- `POST /wifi/status` is used by firmware to report connected SSID, IP, RSSI, and status.

Example dashboard connect payload:

```json
{
  "ssid": "IncubatorLab",
  "password": "network-password"
}
```

## Relay

`POST /relay`

```json
{
  "mode": "AUTO",
  "relay": false,
  "reason": "operator command"
}
```

Modes: `AUTO`, `MANUAL`, `EMERGENCY_OFF`.

## Other Endpoints

- `POST /calibration`
- `POST /restart`
- `POST /ota`
- `GET /system`
- `GET /alerts`
- `POST /alerts/{id}/ack`
- `WS /ws/live`

## Analytics Upgrade

The additive analytics layer adds:

- `GET /incubation`, `POST /incubation`, `PATCH /incubation/{profile_id}`
- `GET /servo`, `POST /servo`
- `GET /heater`
- `GET /power`, `POST /power`
- `GET /system-health`
- `GET /history/servo`, `/history/heater`, `/history/power`, `/history/alarm`, `/history/system-health`

See `docs/ANALYTICS_UPGRADE.md` for the full feature summary.

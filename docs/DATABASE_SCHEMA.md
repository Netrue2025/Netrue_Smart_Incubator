# Database Schema

SQLite database: `backend/data/incubator.db`

## `sensor_readings`

Stores temperature, humidity, heat index, heater relay state, fan relay state, WiFi state, sync status, device timestamp, and server timestamp.

## `relay_events`

Stores relay state transitions and operator or firmware reasons.

## `device_settings`

Stores target temperature, target humidity, tolerance, hysteresis, relay mode, manual relay state, emergency OFF, calibration offsets, timezone, intervals, and update timestamp.

## `alerts`

Stores high/low temperature, high/low humidity, sensor disconnected, WiFi disconnected, storage full, and sync failure alerts.

## `sync_queue`

Stores pending incoming/outgoing sync payloads with status and timestamps.

## `events`

Stores operator and system events.

## Analytics Tables

- `incubation_profiles`: active and previous hatch batches, bird defaults, hatch countdown inputs, and tray-turning stop day.
- `servo_history`: recorded tray servo cycle events and failures.
- `heater_history`: optional persisted heater runtime intervals for future firmware/backend enrichments.
- `power_config`: wattage, voltage, and tariff values used for power estimates.
- `power_history`: optional persisted power metrics.
- `alarm_history`: hardware/software alarm lifecycle, mute, and resolve state.
- `health_history`: optional hardware health snapshots.

These tables are additive and do not replace the existing telemetry, relay, settings, alert, queue, or event tables.

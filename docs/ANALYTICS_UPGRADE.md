# Smart Incubator V2 Analytics Upgrade

This upgrade is additive. Existing ESP32 sensor posting, relay control, tray servo settings, OLED behavior, alerts, and dashboard pages remain in place.

## New Dashboard Areas

- Incubation Profile: bird category, egg count, loading date, hatch countdown, lockdown day, target temperature/humidity, and tray-turning stop day.
- Servo Analytics: configured tray angle, interval, slow speed, expected cycles per day, recorded cycle history, and daily failures.
- Heater Analytics: relay cycles, runtime, duty cycle, and temperature stability over the last 24 hours.
- Power Management: configurable heater/fan/controller/servo wattage, grid voltage, tariff, estimated kWh, current draw, and cost.
- System Health: backend, database, ESP32 telemetry freshness, DHT sensor presence, WiFi, relay state, servo state, queue size, and open alerts.

## New API Endpoints

All endpoints use the existing `/api` prefix.

- `GET /api/incubation`
- `POST /api/incubation`
- `PATCH /api/incubation/{profile_id}`
- `GET /api/servo`
- `POST /api/servo`
- `GET /api/heater`
- `GET /api/power`
- `POST /api/power`
- `GET /api/system-health`
- `GET /api/history/servo`
- `GET /api/history/heater`
- `GET /api/history/power`
- `GET /api/history/alarm`
- `GET /api/history/system-health`

## New Database Tables

- `incubation_profiles`
- `servo_history`
- `heater_history`
- `power_config`
- `power_history`
- `alarm_history`
- `health_history`

The backend creates these tables with `Base.metadata.create_all()` during startup. No existing table is rewritten for this feature.

## Notes

- Heater and power analytics are estimated from existing relay events and configured wattage values.
- Servo history is ready for firmware telemetry, but the current firmware can keep running without posting servo events.
- The health monitor is read-only except alarm mute/resolve support for entries in `alarm_history`.

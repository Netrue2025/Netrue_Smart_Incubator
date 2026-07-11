# Troubleshooting Guide

## Backend Will Not Start

- Confirm port `8000` is free.
- Confirm dependencies are installed in the active virtual environment.
- Delete only the database file if you intentionally want a clean database.

## Dashboard Shows Waiting

- Start the backend.
- Confirm the frontend proxy points to port `8000`.
- Confirm the ESP32 can reach `BACKEND_URL`.

## ESP32 Offline

- Check `include/secrets.h`.
- Confirm the router allows device-to-PC traffic.
- Watch the serial monitor for WiFi status.

## Temperature Not Changing

- Verify DHT22 data on GPIO4.
- Add a DHT22 pull-up if using a bare sensor.
- Firmware turns relay OFF after repeated sensor failures.

## Relay Chatter

- Increase tolerance or hysteresis from the Control page.
- Confirm the heater and sensor are physically separated enough to avoid local hot spots.

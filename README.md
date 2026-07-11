# Smart AI Incubator V2

Offline-first ESP32 incubator architecture with a FastAPI backend, React dashboard, PlatformIO firmware, and production documentation.

## Structure

```text
backend/   FastAPI, SQLite, REST, WebSocket, local queues
frontend/  React, Vite, TypeScript, TailwindCSS, Recharts
firmware/  ESP32 DevKit, Arduino framework, DHT22, SSD1306 OLED, heater relay, fan relay, tray servo, buzzer, status LED, page button
docs/      Installation, API, deployment, protocol, sync, troubleshooting
```

## Quick Start

1. Start the backend from `backend/`.
2. Start the frontend from `frontend/`.
3. Copy `firmware/include/secrets.example.h` to `firmware/include/secrets.h`, set WiFi and backend URL, then flash with PlatformIO.

The ESP32 continues temperature control without WiFi and uploads queued readings when connectivity returns.
For Vercel, keep FastAPI reachable through a public HTTPS backend URL or tunnel; the deployed dashboard reads ESP32 telemetry from that backend while local development still uses the Vite `/api` proxy.

GPIO23 drives the fan relay. The firmware keeps the fan ON while humidity is above the target humidity; when humidity is equal to or below target, the fan follows the heater relay.

New local alarm/control pins:

| Module | GPIO |
| --- | --- |
| Buzzer signal | GPIO25 |
| Status LED | GPIO26 |
| Page push button | GPIO27 to GND |

After the animated `NETRUE LTD` boot screen, the OLED stays on temperature/humidity. Press the GPIO27 button to view the other screens one by one; they automatically return to the main screen after 5 seconds. The LED stays ON while powered and blinks during detected faults. The buzzer beeps for 30 seconds when a firmware-detectable fault starts, including `CHECK HEATER` when relay-on heating drops to 36.9 C and is still falling, and `CHECK RELAY` when temperature reaches 39.0 C and keeps rising. If temperature reaches 33.0 C, the OLED shows `CRITICAL TEMP` and the buzzer sounds for at least 2 minutes, continuing longer while the critical low-temperature fault remains active.

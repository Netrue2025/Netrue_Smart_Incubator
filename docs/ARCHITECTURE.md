# Architecture Diagram

```text
React Dashboard
  | REST + 5-second HTTP polling
FastAPI Backend
  | Hostinger MySQL, alerts, settings validation, database queue
Cloud or Local Network
  | JSON over HTTP
ESP32 Firmware
  | DHT22, relay, SSD1306 OLED, SPIFFS queue, Preferences config
Incubator Hardware
```

## Responsibilities

- Firmware keeps incubation safe even when offline.
- Backend stores history in MySQL, validates commands, raises alerts, and serves live state through polling.
- Frontend provides monitoring, control, exports, alerts, system views, and dark mode.

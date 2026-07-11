# Architecture Diagram

```text
React Dashboard
  | REST + WebSocket
FastAPI Backend
  | SQLite, alerts, settings validation, sync queue
Local Network
  | JSON over HTTP
ESP32 Firmware
  | DHT22, relay, SSD1306 OLED, SPIFFS queue, Preferences config
Incubator Hardware
```

## Responsibilities

- Firmware keeps incubation safe even when offline.
- Backend stores history, validates commands, raises alerts, and streams live state.
- Frontend provides monitoring, control, exports, alerts, system views, and dark mode.

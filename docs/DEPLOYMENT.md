# Deployment Guide

## Backend

Run with Uvicorn behind a reverse proxy or as a Windows service.

```powershell
cd backend
.\.venv\Scripts\uvicorn main:app --host 0.0.0.0 --port 8000
```

Keep `backend/data` on persistent storage and back it up regularly.

## Frontend

```powershell
cd frontend
npm run build
```

Serve `frontend/dist` with Nginx, Caddy, or any static file server. Proxy `/api` and `/ws` to the backend.

## Firmware

Set `BACKEND_URL` to the LAN IP or domain that reaches the backend. Confirm the ESP32 and backend are on the same network before field use.

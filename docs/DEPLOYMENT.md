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

### Vercel dashboard with a local backend

The Vercel deployment is a static dashboard. It cannot receive ESP32 telemetry by
itself; the ESP32 still posts readings to the FastAPI backend at
`POST /api/environment`, and the dashboard reads those readings from the backend.

For local development, keep using:

```text
Vite dashboard -> /api -> http://localhost:8000
ESP32 -> http://YOUR-LAN-IP:8000/api
```

For the deployed dashboard at `https://netrue-smart-incubator.vercel.app/`, the
browser must be able to reach the backend through HTTPS. Use either a hosted
FastAPI backend or an HTTPS tunnel to your local backend. Then open the deployed
dashboard, go to Settings, and set **Backend API URL** to the public backend URL,
for example:

```text
https://your-backend-domain.com
```

The dashboard automatically appends `/api` when needed and connects WebSockets
to `/ws/live` on the same backend. The backend CORS defaults include the Vercel
domain and Vercel preview domains.

If the backend is still running on your local machine, the ESP32 can continue to
use the LAN address in `BACKEND_URL`, while the deployed dashboard uses the
public HTTPS tunnel URL. Both URLs point to the same FastAPI process and SQLite
data.

## Firmware

Set `BACKEND_URL` to the LAN IP or domain that reaches the backend. Confirm the ESP32 and backend are on the same network before field use.

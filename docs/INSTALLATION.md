# Installation Guide

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Vercel Frontend Deployment

This project keeps the web dashboard inside `frontend/`. The root `vercel.json`
configures Vercel to install dependencies in that folder, run the Vite build,
and publish `frontend/dist`.

If the FastAPI backend is hosted on another server, add this Vercel environment
variable before deploying:

```text
VITE_API_BASE_URL=https://your-backend-domain.com/api
```

If you do not set it, the dashboard will call `/api` on the same domain. You can
also open the deployed dashboard, go to Settings, and set **Backend API URL** at
runtime. For a backend running on your local machine, expose `localhost:8000`
through an HTTPS tunnel and use that public HTTPS URL in the deployed dashboard;
the ESP32 may still use your LAN `BACKEND_URL`.

## Firmware

```powershell
cd firmware
copy include\secrets.example.h include\secrets.h
pio run -t upload
pio device monitor
```

Set `BACKEND_URL` in `include/secrets.h` to the IP address of the backend host.

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
publish `frontend/dist`, and route `/api/...` to the FastAPI app through
`api/index.py`.

For a full Vercel deployment, set Hostinger MySQL environment variables:

```text
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:3306/DATABASE?charset=utf8mb4
DB_HOST=HOST
DB_PORT=3306
DB_NAME=DATABASE
DB_USER=USER
DB_PASSWORD=PASSWORD
```

Run `alembic upgrade head` from the repository root against the same database
before the ESP32 starts posting production telemetry.

Then set the ESP32 firmware backend URL to the deployed Vercel origin:

```cpp
#define BACKEND_URL "https://netrue-smart-incubator.vercel.app"
```

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

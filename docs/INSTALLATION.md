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

## Firmware

```powershell
cd firmware
copy include\secrets.example.h include\secrets.h
pio run -t upload
pio device monitor
```

Set `BACKEND_URL` in `include/secrets.h` to the IP address of the backend host.

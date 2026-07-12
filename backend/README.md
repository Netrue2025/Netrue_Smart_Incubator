# Smart AI Incubator V2 Backend

FastAPI service for telemetry storage, validated control settings, relay commands, alerts, database-backed queues, and live HTTP polling.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Configure MySQL before running. From the repository root, run:

```powershell
$env:DB_HOST="your-hostinger-mysql-host"
$env:DB_PORT="3306"
$env:DB_NAME="your_database"
$env:DB_USER="your_user"
$env:DB_PASSWORD="your_password"
alembic upgrade head
```

If Windows `venv` fails because `ensurepip` is broken, install Python 3.13+ with pip enabled or install dependencies into a local target folder:

```powershell
py -3.13 -m pip install -r requirements.txt -t .pythonlibs
py -3.13 main.py
```

Use `py -3.13 main.py` on this Windows machine if the default `python` command points to Python 3.14. The checked-in `main.py` automatically loads dependencies from `.pythonlibs` when that folder exists.

## API

- `GET /api/status`
- `GET /api/environment`
- `POST /api/environment`
- `GET /api/history?range=today|week|month|custom`
- `GET /api/settings`
- `POST /api/settings`
- `POST /api/relay`
- `POST /api/calibration`
- `POST /api/restart`
- `POST /api/ota`
- `GET /api/system`
- `GET /api/alerts`
- `POST /api/alerts/{id}/ack`
- `GET /api/live/status`
- `GET /api/reports/power.pdf`
- `GET /api/reports/power.csv`
- `GET /api/reports/power.xlsx`

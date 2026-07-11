from datetime import datetime

from fastapi import APIRouter, Depends, Query, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.analytics import router as analytics_router
from app.database.session import get_db
from app.models.entities import Alert
from app.queue.offline_queue import enqueue
from app.schemas.api import AlertOut, ApiMessage, CalibrationIn, EnvironmentIn, EnvironmentOut, RelayCommand, SettingsIn, SettingsOut
from app.services.incubator import (
    apply_calibration,
    apply_relay_command,
    get_history,
    get_or_create_settings,
    ingest_environment,
    latest_reading,
    reading_to_payload,
    status_snapshot,
    system_snapshot,
    update_settings,
)

router = APIRouter()
router.include_router(analytics_router)


@router.get("/status")
def get_status(db: Session = Depends(get_db)) -> dict:
    return status_snapshot(db)


@router.get("/environment")
def get_environment(db: Session = Depends(get_db)) -> dict | None:
    return reading_to_payload(latest_reading(db))


@router.post("/environment", response_model=EnvironmentOut)
def post_environment(payload: EnvironmentIn, db: Session = Depends(get_db)) -> EnvironmentOut:
    return ingest_environment(db, payload)


@router.get("/history")
def history(
    range: str = Query(default="today", pattern="^(today|week|month|custom)$"),
    start: datetime | None = None,
    end: datetime | None = None,
    db: Session = Depends(get_db),
) -> dict:
    return get_history(db, range, start, end)


@router.get("/settings", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db)) -> SettingsOut:
    return get_or_create_settings(db)


@router.post("/settings", response_model=SettingsOut)
def post_settings(payload: SettingsIn, db: Session = Depends(get_db)) -> SettingsOut:
    return update_settings(db, payload)


@router.post("/relay", response_model=SettingsOut)
def post_relay(payload: RelayCommand, db: Session = Depends(get_db)) -> SettingsOut:
    return apply_relay_command(db, payload)


@router.post("/calibration", response_model=SettingsOut)
def post_calibration(payload: CalibrationIn, db: Session = Depends(get_db)) -> SettingsOut:
    return apply_calibration(db, payload)


@router.post("/restart", response_model=ApiMessage)
def restart_device(db: Session = Depends(get_db)) -> ApiMessage:
    enqueue(db, "outgoing", "restart", {"command": "restart", "timestamp": datetime.utcnow().isoformat()})
    return ApiMessage(message="Restart command queued for the ESP32")


@router.post("/ota", response_model=ApiMessage)
async def ota_update(file: UploadFile | None = None, db: Session = Depends(get_db)) -> ApiMessage:
    payload = {"command": "ota", "filename": file.filename if file else None, "timestamp": datetime.utcnow().isoformat()}
    enqueue(db, "outgoing", "ota", payload)
    return ApiMessage(message="OTA update command queued")


@router.get("/system")
def system(db: Session = Depends(get_db)) -> dict:
    return system_snapshot(db)


@router.get("/alerts", response_model=list[AlertOut])
def alerts(db: Session = Depends(get_db)) -> list[Alert]:
    return db.scalars(select(Alert).order_by(desc(Alert.created_at)).limit(100)).all()


@router.post("/alerts/{alert_id}/ack", response_model=ApiMessage)
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)) -> ApiMessage:
    alert = db.get(Alert, alert_id)
    if not alert:
        return JSONResponse(status_code=404, content={"ok": False, "message": "Alert not found"})
    alert.acknowledged = True
    db.add(alert)
    db.commit()
    return ApiMessage(message="Alert acknowledged")

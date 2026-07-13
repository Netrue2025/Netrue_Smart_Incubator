from datetime import date, datetime

from fastapi import APIRouter, Depends, Query, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.analytics import router as analytics_router
from app.database.session import get_db
from app.models.entities import Alert
from app.queue.offline_queue import enqueue
from app.reports import power_report_response
from app.schemas.api import (
    AlertDeleteIn,
    AlertOut,
    ApiMessage,
    CalibrationIn,
    EnvironmentIn,
    EnvironmentOut,
    NotificationSettingsIn,
    NotificationSettingsOut,
    RelayCommand,
    SettingsIn,
    SettingsOut,
    WifiConnectIn,
    WifiNetworkOut,
    WifiNetworksIn,
    WifiStatusIn,
)
from app.services.incubator import (
    apply_calibration,
    apply_relay_command,
    get_history,
    get_or_create_settings,
    ingest_environment,
    latest_reading,
    live_status_snapshot,
    reading_to_payload,
    request_wifi_scan,
    status_snapshot,
    system_snapshot,
    save_wifi_credentials,
    update_settings,
    update_wifi_networks,
    update_wifi_status,
    wifi_network_rows,
    settings_to_payload,
)
from app.services.notifications import get_notification_settings, save_notification_settings

router = APIRouter()
router.include_router(analytics_router)


@router.get("/status")
def get_status(db: Session = Depends(get_db)) -> dict:
    return status_snapshot(db)


@router.get("/live/status")
def get_live_status(db: Session = Depends(get_db)) -> dict:
    return live_status_snapshot(db)


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


@router.get("/settings")
def get_settings(firmware: bool = False, db: Session = Depends(get_db)) -> dict:
    return settings_to_payload(get_or_create_settings(db), include_wifi_secret=firmware)


@router.post("/settings", response_model=SettingsOut)
def post_settings(payload: SettingsIn, db: Session = Depends(get_db)) -> SettingsOut:
    return update_settings(db, payload)


@router.get("/wifi/networks", response_model=list[WifiNetworkOut])
def wifi_networks(db: Session = Depends(get_db)) -> list:
    return wifi_network_rows(db)


@router.post("/wifi/scan", response_model=SettingsOut)
def post_wifi_scan(db: Session = Depends(get_db)) -> SettingsOut:
    return request_wifi_scan(db)


@router.post("/wifi/connect", response_model=SettingsOut)
def post_wifi_connect(payload: WifiConnectIn, db: Session = Depends(get_db)) -> SettingsOut:
    return save_wifi_credentials(db, payload)


@router.post("/wifi/networks", response_model=list[WifiNetworkOut])
def post_wifi_networks(payload: WifiNetworksIn, db: Session = Depends(get_db)) -> list:
    return update_wifi_networks(db, payload)


@router.post("/wifi/status", response_model=SettingsOut)
def post_wifi_status(payload: WifiStatusIn, db: Session = Depends(get_db)) -> SettingsOut:
    return update_wifi_status(db, payload)


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


@router.get("/reports/power.{export_format}")
def export_power_report(export_format: str, day: date | None = None, db: Session = Depends(get_db)):
    if export_format not in {"pdf", "csv", "xlsx"}:
        return JSONResponse(status_code=400, content={"ok": False, "message": "Unsupported report format"})
    return power_report_response(db, export_format, day=day)


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


@router.delete("/alerts/{alert_id}", response_model=ApiMessage)
def delete_alert(alert_id: int, db: Session = Depends(get_db)) -> ApiMessage:
    alert = db.get(Alert, alert_id)
    if not alert:
        return JSONResponse(status_code=404, content={"ok": False, "message": "Alert not found"})
    db.delete(alert)
    db.commit()
    return ApiMessage(message="Alert deleted")


@router.post("/alerts/delete", response_model=ApiMessage)
def delete_alerts(payload: AlertDeleteIn, db: Session = Depends(get_db)) -> ApiMessage:
    if not payload.ids:
        return ApiMessage(message="No alerts selected")
    rows = db.scalars(select(Alert).where(Alert.id.in_(payload.ids))).all()
    for row in rows:
        db.delete(row)
    db.commit()
    return ApiMessage(message=f"Deleted {len(rows)} alert(s)")


@router.get("/notifications", response_model=NotificationSettingsOut)
def notification_settings(db: Session = Depends(get_db)) -> dict:
    return get_notification_settings(db)


@router.post("/notifications", response_model=NotificationSettingsOut)
def save_notifications(payload: NotificationSettingsIn, db: Session = Depends(get_db)) -> dict:
    return save_notification_settings(db, payload)

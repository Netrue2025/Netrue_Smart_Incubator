from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.analytics import AlarmPatch, IncubationProfileIn, IncubationProfilePatch, PowerConfigIn, ServoEventIn
from app.services.analytics import (
    active_profile,
    create_profile,
    heater_summary,
    history_rows,
    list_profiles,
    power_summary,
    profile_payload,
    record_servo_event,
    servo_summary,
    system_health,
    update_power_config,
    update_profile,
)

router = APIRouter()


@router.get("/incubation")
def get_incubation(db: Session = Depends(get_db)) -> dict:
    profile = active_profile(db)
    return {"active": profile_payload(profile) if profile else None, "profiles": list_profiles(db)}


@router.post("/incubation")
def post_incubation(payload: IncubationProfileIn, db: Session = Depends(get_db)) -> dict:
    return create_profile(db, payload)


@router.patch("/incubation/{profile_id}")
def patch_incubation(profile_id: int, payload: IncubationProfilePatch, db: Session = Depends(get_db)) -> dict:
    profile = update_profile(db, profile_id, payload)
    if not profile:
        return JSONResponse(status_code=404, content={"ok": False, "message": "Incubation profile not found"})
    return profile


@router.get("/servo")
def get_servo(db: Session = Depends(get_db)) -> dict:
    return servo_summary(db)


@router.post("/servo")
def post_servo(payload: ServoEventIn, db: Session = Depends(get_db)) -> dict:
    return record_servo_event(db, payload)


@router.get("/heater")
def get_heater(db: Session = Depends(get_db)) -> dict:
    return heater_summary(db)


@router.get("/power")
def get_power(day: date | None = None, db: Session = Depends(get_db)) -> dict:
    return power_summary(db, log=False, day=day)


@router.post("/power")
def post_power(payload: PowerConfigIn, db: Session = Depends(get_db)) -> dict:
    update_power_config(db, payload)
    return power_summary(db)


@router.get("/system-health")
def get_system_health(db: Session = Depends(get_db)) -> dict:
    return system_health(db)


@router.post("/system-health/alarms/{alarm_id}")
def patch_alarm(alarm_id: int, payload: AlarmPatch, db: Session = Depends(get_db)) -> dict:
    from app.models.entities import AlarmHistory, now_utc

    alarm = db.get(AlarmHistory, alarm_id)
    if not alarm:
        return JSONResponse(status_code=404, content={"ok": False, "message": "Alarm not found"})
    if payload.muted is not None:
        alarm.muted = payload.muted
    if payload.resolved is not None:
        alarm.resolved = payload.resolved
        alarm.resolved_at = now_utc() if payload.resolved else None
        if alarm.resolved_at:
            alarm.duration_seconds = max(0.0, (alarm.resolved_at - alarm.started_at).total_seconds())
    db.add(alarm)
    db.commit()
    return {"ok": True, "message": "Alarm updated"}


@router.get("/history/servo")
def get_servo_history(limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)) -> dict:
    return {"items": history_rows(db, "servo", limit)}


@router.get("/history/heater")
def get_heater_history(limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)) -> dict:
    return {"items": history_rows(db, "heater", limit)}


@router.get("/history/power")
def get_power_history(limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)) -> dict:
    return {"items": history_rows(db, "power", limit)}


@router.get("/history/alarm")
def get_alarm_history(limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)) -> dict:
    return {"items": history_rows(db, "alarm", limit)}


@router.get("/history/system-health")
def get_health_history(limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)) -> dict:
    return {"items": history_rows(db, "health", limit)}

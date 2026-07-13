from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.entities import (
    AlarmHistory,
    Alert,
    HealthHistory,
    HeaterHistory,
    IncubationProfile,
    PowerConfig,
    PowerHistory,
    RelayEvent,
    SensorReading,
    ServoHistory,
    now_utc,
)
from app.queue.offline_queue import pending_count
from app.schemas.analytics import IncubationProfileIn, IncubationProfilePatch, PowerConfigIn, ServoEventIn
from app.services.incubator import get_or_create_settings, latest_reading
from app.services.power_service import PowerService
from app.utils.time import ensure_aware_utc


BIRD_DEFAULTS: dict[str, dict[str, float | int]] = {
    "chicken": {"incubation_days": 21, "lockdown_day": 18, "turning_disabled_day": 18, "target_temperature": 37.5, "target_humidity": 60.0},
    "duck": {"incubation_days": 28, "lockdown_day": 25, "turning_disabled_day": 25, "target_temperature": 37.5, "target_humidity": 65.0},
    "quail": {"incubation_days": 17, "lockdown_day": 14, "turning_disabled_day": 14, "target_temperature": 37.5, "target_humidity": 58.0},
    "turkey": {"incubation_days": 28, "lockdown_day": 25, "turning_disabled_day": 25, "target_temperature": 37.5, "target_humidity": 60.0},
    "goose": {"incubation_days": 30, "lockdown_day": 27, "turning_disabled_day": 27, "target_temperature": 37.4, "target_humidity": 65.0},
    "custom": {"incubation_days": 21, "lockdown_day": 18, "turning_disabled_day": 18, "target_temperature": 37.5, "target_humidity": 60.0},
}


def bird_defaults(category: str) -> dict[str, float | int]:
    return BIRD_DEFAULTS.get(category.lower(), BIRD_DEFAULTS["custom"])


def active_profile(db: Session) -> IncubationProfile | None:
    return db.scalars(select(IncubationProfile).where(IncubationProfile.is_active.is_(True)).order_by(desc(IncubationProfile.updated_at)).limit(1)).first()


def profile_payload(profile: IncubationProfile) -> dict[str, Any]:
    today = date.today()
    elapsed_days = max(0, (today - profile.loading_date).days)
    current_day = min(profile.incubation_days, elapsed_days + 1)
    expected_hatch_date = profile.loading_date + timedelta(days=profile.incubation_days)
    lockdown_date = profile.loading_date + timedelta(days=profile.lockdown_day)
    days_remaining = max(0, (expected_hatch_date - today).days)
    progress = min(100.0, max(0.0, (elapsed_days / max(1, profile.incubation_days)) * 100))
    turning_enabled_today = bool(profile.turning_enabled and current_day < profile.turning_disabled_day)
    return {
        "id": profile.id,
        "bird_category": profile.bird_category,
        "custom_bird": profile.custom_bird,
        "batch_name": profile.batch_name,
        "egg_count": profile.egg_count,
        "loading_date": profile.loading_date,
        "incubation_days": profile.incubation_days,
        "lockdown_day": profile.lockdown_day,
        "target_temperature": profile.target_temperature,
        "target_humidity": profile.target_humidity,
        "turning_enabled": profile.turning_enabled,
        "turning_disabled_day": profile.turning_disabled_day,
        "notes": profile.notes,
        "is_active": profile.is_active,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
        "current_day": current_day,
        "days_remaining": days_remaining,
        "progress_percent": round(progress, 1),
        "expected_hatch_date": expected_hatch_date,
        "lockdown_date": lockdown_date,
        "turning_enabled_today": turning_enabled_today,
    }


def list_profiles(db: Session) -> list[dict[str, Any]]:
    profiles = db.scalars(select(IncubationProfile).order_by(desc(IncubationProfile.is_active), desc(IncubationProfile.updated_at))).all()
    return [profile_payload(profile) for profile in profiles]


def create_profile(db: Session, payload: IncubationProfileIn) -> dict[str, Any]:
    defaults = bird_defaults(payload.bird_category)
    data = payload.model_dump()
    for key, value in defaults.items():
        if data.get(key) is None:
            data[key] = value
    if data["is_active"]:
        db.query(IncubationProfile).update({IncubationProfile.is_active: False})
    profile = IncubationProfile(**data, updated_at=now_utc())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile_payload(profile)


def update_profile(db: Session, profile_id: int, payload: IncubationProfilePatch) -> dict[str, Any] | None:
    profile = db.get(IncubationProfile, profile_id)
    if not profile:
        return None
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("is_active") is True:
        db.query(IncubationProfile).where(IncubationProfile.id != profile_id).update({IncubationProfile.is_active: False})
    for key, value in updates.items():
        setattr(profile, key, value)
    profile.updated_at = now_utc()
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile_payload(profile)


def get_power_config(db: Session) -> PowerConfig:
    config = db.get(PowerConfig, 1)
    if config:
        changed = False
        if config.fan_watts == 2.5:
            config.fan_watts = 3.0
            changed = True
        if config.controller_watts == 3.0:
            config.controller_watts = 1.0
            changed = True
        if getattr(config, "servo_average_watts", 0.0) == 0.0:
            config.servo_average_watts = 0.1
            changed = True
        if config.buzzer_watts == 0.5:
            config.buzzer_watts = 0.0
            changed = True
        if changed:
            db.add(config)
            db.commit()
            db.refresh(config)
        return config
    config = PowerConfig(id=1)
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def update_power_config(db: Session, payload: PowerConfigIn) -> PowerConfig:
    config = get_power_config(db)
    for key, value in payload.model_dump().items():
        setattr(config, key, value)
    config.updated_at = now_utc()
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def relay_runtime(db: Session, begin: datetime, finish: datetime) -> dict[str, Any]:
    events = db.scalars(select(RelayEvent).where(RelayEvent.created_at >= begin, RelayEvent.created_at <= finish).order_by(RelayEvent.created_at)).all()
    total_seconds = 0.0
    cycles = 0
    on_at: datetime | None = None
    for event in events:
        event_time = ensure_aware_utc(event.created_at)
        if event.relay and on_at is None:
            on_at = event_time
            cycles += 1
        elif not event.relay and on_at is not None:
            total_seconds += max(0.0, (event_time - on_at).total_seconds())
            on_at = None
    if on_at is not None:
        total_seconds += max(0.0, (finish - on_at).total_seconds())
    return {"seconds": total_seconds, "cycles": cycles, "events": events, "currently_on": on_at is not None}


def heater_summary(db: Session) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    begin = now - timedelta(hours=24)
    runtime = relay_runtime(db, begin, now)
    readings = db.scalars(select(SensorReading).where(SensorReading.created_at >= begin).order_by(SensorReading.created_at)).all()
    average_temp = sum(reading.temperature for reading in readings) / len(readings) if readings else None
    min_temp = min((reading.temperature for reading in readings), default=None)
    max_temp = max((reading.temperature for reading in readings), default=None)
    duty_cycle = (runtime["seconds"] / 86400) * 100
    return {
        "window_hours": 24,
        "cycles": runtime["cycles"],
        "runtime_seconds": round(runtime["seconds"], 1),
        "runtime_minutes": round(runtime["seconds"] / 60, 1),
        "duty_cycle_percent": round(duty_cycle, 1),
        "currently_on": runtime["currently_on"],
        "average_temperature": round(average_temp, 2) if average_temp is not None else None,
        "min_temperature": min_temp,
        "max_temperature": max_temp,
        "recent_events": [
            {"id": event.id, "relay": event.relay, "mode": event.mode, "reason": event.reason, "created_at": event.created_at}
            for event in reversed(runtime["events"][-12:])
        ],
    }


def servo_summary(db: Session) -> dict[str, Any]:
    settings = get_or_create_settings(db)
    profile = active_profile(db)
    now = datetime.now(timezone.utc)
    begin = now.replace(hour=0, minute=0, second=0, microsecond=0)
    completed_today = db.scalar(select(func.count(ServoHistory.id)).where(ServoHistory.created_at >= begin, ServoHistory.success.is_(True))) or 0
    failures_today = db.scalar(select(func.count(ServoHistory.id)).where(ServoHistory.created_at >= begin, ServoHistory.success.is_(False))) or 0
    latest = db.scalars(select(ServoHistory).order_by(desc(ServoHistory.created_at)).limit(1)).first()
    interval = max(1, settings.tray_servo_interval_minutes)
    expected_cycles = int(1440 / interval) if settings.tray_servo_enabled else 0
    return {
        "enabled": settings.tray_servo_enabled,
        "target_angle": settings.tray_servo_angle,
        "interval_minutes": interval,
        "speed_dps": settings.tray_servo_speed_dps,
        "expected_cycles_per_day": expected_cycles,
        "completed_today": completed_today,
        "failures_today": failures_today,
        "profile_turning_enabled": bool(profile and profile_payload(profile)["turning_enabled_today"]),
        "last_event": {
            "id": latest.id,
            "event_type": latest.event_type,
            "success": latest.success,
            "target_angle": latest.target_angle,
            "duration_seconds": latest.duration_seconds,
            "message": latest.message,
            "created_at": latest.created_at,
        }
        if latest
        else None,
    }


def record_servo_event(db: Session, payload: ServoEventIn) -> dict[str, Any]:
    profile = active_profile(db)
    event = ServoHistory(profile_id=profile.id if profile else None, **payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return {
        "id": event.id,
        "profile_id": event.profile_id,
        "event_type": event.event_type,
        "success": event.success,
        "target_angle": event.target_angle,
        "duration_seconds": event.duration_seconds,
        "message": event.message,
        "created_at": event.created_at,
    }


def power_summary(db: Session, log: bool = True, day: date | None = None) -> dict[str, Any]:
    return PowerService.summary(db, log=log, day=day)


def system_health(db: Session) -> dict[str, Any]:
    settings = get_or_create_settings(db)
    reading = latest_reading(db)
    now = datetime.now(timezone.utc)
    reading_age = (now - ensure_aware_utc(reading.created_at)).total_seconds() if reading else None
    sensor_fresh = reading_age is not None and reading_age <= get_settings().sensor_timeout_seconds
    unacked_alerts = db.scalar(select(func.count(Alert.id)).where(Alert.acknowledged.is_(False))) or 0
    modules = [
        {"module": "backend", "state": "ok", "detail": "FastAPI is responding"},
        {"module": "database", "state": "ok", "detail": "MySQL session is available"},
        {"module": "esp32", "state": "ok" if sensor_fresh else "warning", "detail": "Fresh telemetry received" if sensor_fresh else "Waiting for fresh ESP32 telemetry"},
        {"module": "sensor", "state": "ok" if reading else "warning", "detail": "DHT reading available" if reading else "No DHT reading stored yet"},
        {"module": "wifi", "state": "ok" if reading and reading.wifi else "warning", "detail": "ESP32 WiFi connected" if reading and reading.wifi else "ESP32 WiFi not confirmed"},
        {"module": "relay", "state": "ok" if not settings.emergency_off else "critical", "detail": "Relay control active" if not settings.emergency_off else "Emergency off is active"},
        {"module": "servo", "state": "ok" if settings.tray_servo_enabled else "idle", "detail": "Tray turning enabled" if settings.tray_servo_enabled else "Tray turning disabled"},
    ]
    if unacked_alerts:
        modules.append({"module": "alarms", "state": "warning", "detail": f"{unacked_alerts} unacknowledged alert(s)"})
    bad = sum(1 for module in modules if module["state"] in {"warning", "critical"})
    critical = any(module["state"] == "critical" for module in modules)
    return {
        "state": "critical" if critical else "warning" if bad else "ok",
        "score": max(0, int(100 - bad * 14 - (30 if critical else 0))),
        "checked_at": now,
        "unacknowledged_alerts": unacked_alerts,
        "queue_size": pending_count(db),
        "modules": modules,
    }


def history_rows(db: Session, table: str, limit: int = 100) -> list[dict[str, Any]]:
    limit = min(max(limit, 1), 500)
    if table == "servo":
        rows = db.scalars(select(ServoHistory).order_by(desc(ServoHistory.created_at)).limit(limit)).all()
        return [
            {
                "id": row.id,
                "profile_id": row.profile_id,
                "event_type": row.event_type,
                "success": row.success,
                "target_angle": row.target_angle,
                "duration_seconds": row.duration_seconds,
                "message": row.message,
                "created_at": row.created_at,
            }
            for row in rows
        ]
    if table == "heater":
        rows = db.scalars(select(HeaterHistory).order_by(desc(HeaterHistory.created_at)).limit(limit)).all()
        return [
            {"id": row.id, "relay_event_id": row.relay_event_id, "started_at": row.started_at, "ended_at": row.ended_at, "duration_seconds": row.duration_seconds, "created_at": row.created_at}
            for row in rows
        ]
    if table == "power":
        from app.services.history_service import HistoryService

        return HistoryService.power_history_rows(db, limit)
    if table == "alarm":
        rows = db.scalars(select(AlarmHistory).order_by(desc(AlarmHistory.started_at)).limit(limit)).all()
        return [
            {
                "id": row.id,
                "module": row.module,
                "severity": row.severity,
                "message": row.message,
                "resolved": row.resolved,
                "muted": row.muted,
                "started_at": row.started_at,
                "resolved_at": row.resolved_at,
                "duration_seconds": row.duration_seconds,
            }
            for row in rows
        ]
    rows = db.scalars(select(HealthHistory).order_by(desc(HealthHistory.created_at)).limit(limit)).all()
    return [{"id": row.id, "module": row.module, "state": row.state, "detail": row.detail, "created_at": row.created_at} for row in rows]

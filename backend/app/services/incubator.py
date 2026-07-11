from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.entities import Alert, DeviceSettings, EventLog, RelayEvent, SensorReading, now_utc
from app.queue.offline_queue import enqueue, pending_count
from app.schemas.api import CalibrationIn, EnvironmentIn, RelayCommand, SettingsIn
from app.utils.time import ensure_aware_utc


def get_or_create_settings(db: Session) -> DeviceSettings:
    settings = db.get(DeviceSettings, 1)
    if settings:
        return settings
    settings = DeviceSettings(id=1)
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def latest_reading(db: Session) -> SensorReading | None:
    return db.scalars(select(SensorReading).order_by(desc(SensorReading.created_at)).limit(1)).first()


def create_event(db: Session, type_: str, message: str) -> None:
    db.add(EventLog(type=type_, message=message))
    db.commit()


def create_alert(db: Session, type_: str, severity: str, message: str) -> Alert:
    alert = Alert(type=type_, severity=severity, message=message)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def evaluate_alerts(db: Session, reading: SensorReading, settings: DeviceSettings) -> None:
    high_temp = settings.target_temperature + settings.tolerance
    low_temp = settings.target_temperature - settings.tolerance
    high_humidity = settings.target_humidity + 10
    low_humidity = settings.target_humidity - 10
    checks = [
        (reading.temperature > high_temp, "high_temperature", "critical", f"Temperature {reading.temperature:.1f} C is above safe limit {high_temp:.1f} C"),
        (reading.temperature < low_temp, "low_temperature", "warning", f"Temperature {reading.temperature:.1f} C is below lower limit {low_temp:.1f} C"),
        (reading.humidity > high_humidity, "high_humidity", "warning", f"Humidity {reading.humidity:.1f}% is above target band"),
        (reading.humidity < low_humidity, "low_humidity", "warning", f"Humidity {reading.humidity:.1f}% is below target band"),
        (not reading.wifi, "wifi_disconnected", "warning", "ESP32 reported WiFi disconnected"),
        (reading.sync_status != "synced", "sync_failed", "warning", f"Sync status is {reading.sync_status}"),
    ]
    for active, type_, severity, message in checks:
        if active:
            recent = db.scalars(
                select(Alert)
                .where(Alert.type == type_, Alert.acknowledged.is_(False))
                .order_by(desc(Alert.created_at))
                .limit(1)
            ).first()
            if not recent:
                create_alert(db, type_, severity, message)


def ingest_environment(db: Session, payload: EnvironmentIn) -> SensorReading:
    heat_index = payload.heat_index
    if heat_index is None:
        heat_index = payload.temperature + 0.33 * (payload.humidity / 100 * 6.105) - 0.7
    reading = SensorReading(
        temperature=payload.temperature,
        humidity=payload.humidity,
        heat_index=heat_index,
        relay=payload.relay,
        fan_relay=payload.fan_relay,
        wifi=payload.wifi,
        sync_status=payload.sync_status,
        device_timestamp=ensure_aware_utc(payload.timestamp),
    )
    db.add(reading)
    latest = latest_reading(db)
    if latest is None or latest.relay != reading.relay:
        db.add(RelayEvent(relay=reading.relay, mode=get_or_create_settings(db).relay_mode, reason="firmware telemetry"))
    db.commit()
    db.refresh(reading)
    evaluate_alerts(db, reading, get_or_create_settings(db))
    return reading


def update_settings(db: Session, payload: SettingsIn) -> DeviceSettings:
    settings = get_or_create_settings(db)
    incoming_ts = ensure_aware_utc(payload.timestamp)
    current_ts = ensure_aware_utc(settings.updated_at)
    if incoming_ts < current_ts:
        enqueue(db, "incoming", "settings_conflict", payload.model_dump(mode="json"))
        return settings
    updates = payload.model_dump(exclude={"timestamp"}, exclude_none=True)
    for key, value in updates.items():
        setattr(settings, key, value)
    if settings.emergency_off:
        settings.relay_mode = "EMERGENCY_OFF"
        settings.manual_relay = False
    settings.updated_at = incoming_ts
    db.add(settings)
    db.commit()
    db.refresh(settings)
    enqueue(db, "outgoing", "settings", settings_to_command(settings))
    create_event(db, "settings_updated", "Incubator settings changed")
    return settings


def settings_to_command(settings: DeviceSettings) -> dict[str, Any]:
    return {
        "targetTemp": settings.target_temperature,
        "targetHumidity": settings.target_humidity,
        "tolerance": settings.tolerance,
        "hysteresis": settings.hysteresis,
        "relayMode": settings.relay_mode,
        "manualRelay": settings.manual_relay,
        "emergencyOff": settings.emergency_off,
        "trayServoEnabled": settings.tray_servo_enabled,
        "trayServoAngle": settings.tray_servo_angle,
        "trayServoIntervalMinutes": settings.tray_servo_interval_minutes,
        "trayServoSpeedDps": settings.tray_servo_speed_dps,
        "timestamp": settings.updated_at.isoformat(),
    }


def reading_to_payload(reading: SensorReading | None) -> dict[str, Any] | None:
    if reading is None:
        return None
    return {
        "id": reading.id,
        "temperature": reading.temperature,
        "humidity": reading.humidity,
        "heat_index": reading.heat_index,
        "relay": reading.relay,
        "fan_relay": reading.fan_relay,
        "wifi": reading.wifi,
        "sync_status": reading.sync_status,
        "timestamp": reading.device_timestamp,
        "device_timestamp": reading.device_timestamp,
        "created_at": reading.created_at,
    }


def settings_to_payload(settings: DeviceSettings) -> dict[str, Any]:
    return {
        "id": settings.id,
        "device_name": settings.device_name,
        "timezone": settings.timezone,
        "target_temperature": settings.target_temperature,
        "target_humidity": settings.target_humidity,
        "tolerance": settings.tolerance,
        "hysteresis": settings.hysteresis,
        "sampling_interval": settings.sampling_interval,
        "sync_interval": settings.sync_interval,
        "temperature_offset": settings.temperature_offset,
        "humidity_offset": settings.humidity_offset,
        "relay_mode": settings.relay_mode,
        "manual_relay": settings.manual_relay,
        "emergency_off": settings.emergency_off,
        "tray_servo_enabled": settings.tray_servo_enabled,
        "tray_servo_angle": settings.tray_servo_angle,
        "tray_servo_interval_minutes": settings.tray_servo_interval_minutes,
        "tray_servo_speed_dps": settings.tray_servo_speed_dps,
        "updated_at": settings.updated_at,
    }


def apply_relay_command(db: Session, command: RelayCommand) -> DeviceSettings:
    settings = get_or_create_settings(db)
    settings.relay_mode = command.mode
    settings.manual_relay = command.relay if command.mode == "MANUAL" else False
    settings.emergency_off = command.mode == "EMERGENCY_OFF"
    settings.updated_at = ensure_aware_utc(command.timestamp)
    db.add(settings)
    db.add(RelayEvent(relay=settings.manual_relay, mode=settings.relay_mode, reason=command.reason))
    db.commit()
    db.refresh(settings)
    enqueue(db, "outgoing", "relay", settings_to_command(settings))
    create_event(db, "relay_command", command.reason)
    return settings


def apply_calibration(db: Session, payload: CalibrationIn) -> DeviceSettings:
    return update_settings(
        db,
        SettingsIn(
            temperature_offset=payload.temperature_offset,
            humidity_offset=payload.humidity_offset,
            timestamp=now_utc(),
        ),
    )


def history_window(range_: str, start: datetime | None, end: datetime | None) -> tuple[datetime, datetime]:
    stop = ensure_aware_utc(end)
    if range_ == "custom" and start:
        return ensure_aware_utc(start), stop
    if range_ == "week":
        return stop - timedelta(days=7), stop
    if range_ == "month":
        return stop - timedelta(days=31), stop
    return stop.replace(hour=0, minute=0, second=0, microsecond=0), stop


def get_history(db: Session, range_: str = "today", start: datetime | None = None, end: datetime | None = None) -> dict[str, list[Any]]:
    begin, finish = history_window(range_, start, end)
    readings = db.scalars(
        select(SensorReading)
        .where(SensorReading.created_at >= begin, SensorReading.created_at <= finish)
        .order_by(SensorReading.created_at)
    ).all()
    relay_events = db.scalars(
        select(RelayEvent)
        .where(RelayEvent.created_at >= begin, RelayEvent.created_at <= finish)
        .order_by(RelayEvent.created_at)
    ).all()
    return {"readings": readings, "relay": relay_events}


def status_snapshot(db: Session) -> dict[str, Any]:
    reading = latest_reading(db)
    settings = get_or_create_settings(db)
    now = datetime.now(timezone.utc)
    online = bool(reading and (now - ensure_aware_utc(reading.created_at)).total_seconds() <= get_settings().sensor_timeout_seconds)
    current_reading = reading if online else None
    database_count = db.scalar(select(func.count(SensorReading.id))) or 0
    return {
        "device": {
            "online": online,
            "name": settings.device_name,
            "last_sync": current_reading.created_at if current_reading else None,
            "wifi": current_reading.wifi if current_reading else False,
            "sync_status": current_reading.sync_status if current_reading else "waiting",
        },
        "backend": {"online": True, "database": "ok", "readings": database_count, "queue_size": pending_count(db)},
        "environment": reading_to_payload(current_reading),
        "settings": settings_to_payload(settings),
        "time": now,
    }


def system_snapshot(db: Session) -> dict[str, Any]:
    settings = get_or_create_settings(db)
    reading = latest_reading(db)
    return {
        "firmware_version": get_settings().firmware_version,
        "esp32_chip": "ESP32 DevKit",
        "flash_size": None,
        "free_heap": None,
        "wifi_rssi": None,
        "ip_address": None,
        "mac_address": None,
        "uptime": None,
        "filesystem_usage": None,
        "queue_size": pending_count(db),
        "database_status": "ok",
        "api_status": "ok",
        "settings_updated_at": settings.updated_at,
        "last_reading_at": reading.created_at if reading else None,
    }

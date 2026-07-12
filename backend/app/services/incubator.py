from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.entities import (
    AlarmHistory,
    Alert,
    DeviceSettings,
    EventLog,
    HeaterLog,
    HumidityLog,
    RelayEvent,
    SensorLog,
    SensorReading,
    SystemLog,
    TemperatureLog,
    WifiNetwork,
    now_utc,
)
from app.queue.offline_queue import enqueue, pending_count
from app.schemas.api import CalibrationIn, EnvironmentIn, RelayCommand, SettingsIn, WifiConnectIn, WifiNetworksIn, WifiStatusIn
from app.utils.time import ensure_aware_utc

TEMP_ALERT_LOW_C = 37.0
TEMP_ALERT_HIGH_C = 38.4
HUMIDITY_ALERT_HIGH_PERCENT = 55.0
HUMIDITY_ALERT_THROTTLE = timedelta(hours=1)


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
    db.add(SystemLog(level="info", source=type_, message=message))
    db.commit()


def create_alert(db: Session, type_: str, severity: str, message: str) -> Alert:
    alert = Alert(type=type_, severity=severity, message=message)
    db.add(alert)
    db.add(AlarmHistory(module=type_, severity=severity, message=message))
    db.commit()
    db.refresh(alert)
    return alert


def evaluate_alerts(db: Session, reading: SensorReading, settings: DeviceSettings) -> None:
    now = datetime.now(timezone.utc)
    checks = [
        (reading.temperature > TEMP_ALERT_HIGH_C, "high_temperature", "critical", f"Temperature {reading.temperature:.1f} C is above safe limit {TEMP_ALERT_HIGH_C:.1f} C"),
        (reading.temperature < TEMP_ALERT_LOW_C, "low_temperature", "warning", f"Temperature {reading.temperature:.1f} C is below safe limit {TEMP_ALERT_LOW_C:.1f} C"),
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
    if reading.humidity > HUMIDITY_ALERT_HIGH_PERCENT:
        recent_humidity_alert = db.scalars(
            select(Alert)
            .where(Alert.type == "high_humidity", Alert.created_at >= now - HUMIDITY_ALERT_THROTTLE)
            .order_by(desc(Alert.created_at))
            .limit(1)
        ).first()
        if not recent_humidity_alert:
            create_alert(
                db,
                "high_humidity",
                "warning",
                f"Humidity {reading.humidity:.1f}% is above chicken first-18-days safe limit {HUMIDITY_ALERT_HIGH_PERCENT:.0f}%",
            )


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
    db.add(SensorLog(payload=payload.model_dump_json()))
    db.add(TemperatureLog(value=payload.temperature))
    db.add(HumidityLog(value=payload.humidity))
    latest = latest_reading(db)
    if latest is None or latest.relay != reading.relay:
        db.add(RelayEvent(relay=reading.relay, mode=get_or_create_settings(db).relay_mode, reason="firmware telemetry"))
        db.add(HeaterLog(state="on" if reading.relay else "off", payload=payload.model_dump_json()))
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


def settings_to_payload(settings: DeviceSettings, include_wifi_secret: bool = False) -> dict[str, Any]:
    payload = {
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
        "wifi_ssid": settings.wifi_ssid,
        "wifi_password_set": settings.wifi_password_set,
        "wifi_scan_requested": settings.wifi_scan_requested,
        "wifi_connect_requested": settings.wifi_connect_requested,
        "wifi_active_ssid": settings.wifi_active_ssid,
        "wifi_ip_address": settings.wifi_ip_address,
        "wifi_rssi": settings.wifi_rssi,
        "wifi_connection_status": settings.wifi_connection_status,
        "wifi_last_scan_at": settings.wifi_last_scan_at,
        "wifi_last_connect_at": settings.wifi_last_connect_at,
        "updated_at": settings.updated_at,
    }
    if include_wifi_secret:
        payload["wifi_password"] = settings.wifi_password or ""
    return payload


def request_wifi_scan(db: Session) -> DeviceSettings:
    settings = get_or_create_settings(db)
    settings.wifi_scan_requested = True
    settings.updated_at = now_utc()
    db.add(settings)
    db.commit()
    db.refresh(settings)
    enqueue(db, "outgoing", "wifi_scan", {"command": "wifi_scan", "timestamp": settings.updated_at.isoformat()})
    create_event(db, "wifi_scan_requested", "WiFi scan requested from dashboard")
    return settings


def save_wifi_credentials(db: Session, payload: WifiConnectIn) -> DeviceSettings:
    settings = get_or_create_settings(db)
    password = payload.password if payload.password or payload.ssid != settings.wifi_ssid else settings.wifi_password
    settings.wifi_ssid = payload.ssid
    settings.wifi_password = password
    settings.wifi_connect_requested = True
    settings.wifi_scan_requested = False
    settings.wifi_connection_status = "pending"
    settings.updated_at = ensure_aware_utc(payload.timestamp)
    db.add(settings)
    db.commit()
    db.refresh(settings)
    enqueue(db, "outgoing", "wifi_connect", {"ssid": payload.ssid, "timestamp": settings.updated_at.isoformat()})
    create_event(db, "wifi_credentials_updated", f"WiFi target changed to {payload.ssid}")
    return settings


def update_wifi_networks(db: Session, payload: WifiNetworksIn) -> list[WifiNetwork]:
    seen_at = ensure_aware_utc(payload.timestamp)
    db.query(WifiNetwork).delete()
    rows = [
        WifiNetwork(ssid=item.ssid, rssi=item.rssi, encryption=item.encryption, channel=item.channel, last_seen_at=seen_at)
        for item in payload.networks
    ]
    db.add_all(rows)
    settings = get_or_create_settings(db)
    settings.wifi_scan_requested = False
    settings.wifi_last_scan_at = seen_at
    db.add(settings)
    db.commit()
    create_event(db, "wifi_scan_completed", f"ESP32 reported {len(rows)} WiFi network(s)")
    return wifi_network_rows(db)


def update_wifi_status(db: Session, payload: WifiStatusIn) -> DeviceSettings:
    settings = get_or_create_settings(db)
    status_at = ensure_aware_utc(payload.timestamp)
    settings.wifi_active_ssid = payload.ssid
    settings.wifi_ip_address = payload.ip_address
    settings.wifi_rssi = payload.rssi
    settings.wifi_connection_status = "connected" if payload.connected else payload.status
    settings.wifi_connect_requested = False
    settings.wifi_last_connect_at = status_at
    db.add(settings)
    db.commit()
    db.refresh(settings)
    create_event(db, "wifi_status", f"ESP32 WiFi status: {settings.wifi_connection_status}")
    return settings


def wifi_network_rows(db: Session) -> list[WifiNetwork]:
    return db.scalars(select(WifiNetwork).order_by(desc(WifiNetwork.rssi), WifiNetwork.ssid)).all()


def apply_relay_command(db: Session, command: RelayCommand) -> DeviceSettings:
    settings = get_or_create_settings(db)
    settings.relay_mode = command.mode
    settings.manual_relay = command.relay if command.mode == "MANUAL" else False
    settings.emergency_off = command.mode == "EMERGENCY_OFF"
    settings.updated_at = ensure_aware_utc(command.timestamp)
    db.add(settings)
    db.add(RelayEvent(relay=settings.manual_relay, mode=settings.relay_mode, reason=command.reason))
    db.add(HeaterLog(state="on" if settings.manual_relay else "off", payload=command.model_dump_json()))
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
            "wifi_ssid": settings.wifi_active_ssid,
            "wifi_ip_address": settings.wifi_ip_address,
            "wifi_rssi": settings.wifi_rssi,
            "wifi_connection_status": settings.wifi_connection_status,
        },
        "backend": {"online": True, "database": "ok", "readings": database_count, "queue_size": pending_count(db)},
        "environment": reading_to_payload(current_reading),
        "settings": settings_to_payload(settings),
        "time": now,
    }


def live_status_snapshot(db: Session) -> dict[str, Any]:
    snapshot = status_snapshot(db)
    reading = snapshot["environment"]
    settings = snapshot["settings"]
    power = {
        "battery": None,
        "current_power": None,
        "current_runtime": None,
        "duty_cycle": None,
    }
    try:
        from app.services.analytics import heater_summary, power_summary

        heater = heater_summary(db)
        power_summary_payload = power_summary(db, log=False)
        power = {
            "battery": power_summary_payload.get("battery"),
            "current_power": power_summary_payload.get("live_load_watts"),
            "current_runtime": power_summary_payload.get("heater_runtime_minutes"),
            "duty_cycle": heater.get("duty_cycle_percent"),
        }
    except Exception:
        pass
    snapshot["live"] = {
        "temperature": reading["temperature"] if reading else None,
        "humidity": reading["humidity"] if reading else None,
        "heater": reading["relay"] if reading else False,
        "servo": settings["tray_servo_enabled"],
        "battery": power["battery"],
        "current_power": power["current_power"],
        "current_runtime": power["current_runtime"],
        "duty_cycle": power["duty_cycle"],
        "current_rtc": snapshot["time"],
    }
    return snapshot


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

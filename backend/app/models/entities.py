from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    temperature: Mapped[float] = mapped_column(Float)
    humidity: Mapped[float] = mapped_column(Float)
    heat_index: Mapped[float] = mapped_column(Float)
    relay: Mapped[bool] = mapped_column(Boolean, default=False)
    fan_relay: Mapped[bool] = mapped_column(Boolean, default=False)
    wifi: Mapped[bool] = mapped_column(Boolean, default=True)
    sync_status: Mapped[str] = mapped_column(String(30), default="synced")
    device_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)

    @property
    def timestamp(self) -> datetime:
        return self.device_timestamp


class RelayEvent(Base):
    __tablename__ = "relay_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    relay: Mapped[bool] = mapped_column(Boolean)
    mode: Mapped[str] = mapped_column(String(20), default="AUTO")
    reason: Mapped[str] = mapped_column(String(160), default="telemetry")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)


class DeviceSettings(Base):
    __tablename__ = "device_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    device_name: Mapped[str] = mapped_column(String(80), default="Smart Incubator V2")
    timezone: Mapped[str] = mapped_column(String(80), default="Africa/Lagos")
    target_temperature: Mapped[float] = mapped_column(Float, default=37.5)
    target_humidity: Mapped[float] = mapped_column(Float, default=60.0)
    tolerance: Mapped[float] = mapped_column(Float, default=0.3)
    hysteresis: Mapped[float] = mapped_column(Float, default=0.2)
    sampling_interval: Mapped[int] = mapped_column(Integer, default=1)
    sync_interval: Mapped[int] = mapped_column(Integer, default=10)
    temperature_offset: Mapped[float] = mapped_column(Float, default=0.0)
    humidity_offset: Mapped[float] = mapped_column(Float, default=0.0)
    relay_mode: Mapped[str] = mapped_column(String(20), default="AUTO")
    manual_relay: Mapped[bool] = mapped_column(Boolean, default=False)
    emergency_off: Mapped[bool] = mapped_column(Boolean, default=False)
    tray_servo_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    tray_servo_angle: Mapped[int] = mapped_column(Integer, default=45)
    tray_servo_interval_minutes: Mapped[int] = mapped_column(Integer, default=120)
    tray_servo_speed_dps: Mapped[int] = mapped_column(Integer, default=6)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type: Mapped[str] = mapped_column(String(60), index=True)
    severity: Mapped[str] = mapped_column(String(20), default="warning")
    message: Mapped[str] = mapped_column(String(240))
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)


class SyncQueueItem(Base):
    __tablename__ = "sync_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    direction: Mapped[str] = mapped_column(String(20), index=True)
    topic: Mapped[str] = mapped_column(String(80), index=True)
    payload: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EventLog(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type: Mapped[str] = mapped_column(String(80), index=True)
    message: Mapped[str] = mapped_column(String(240))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)


class IncubationProfile(Base):
    __tablename__ = "incubation_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bird_category: Mapped[str] = mapped_column(String(40), default="chicken", index=True)
    custom_bird: Mapped[str | None] = mapped_column(String(80), nullable=True)
    batch_name: Mapped[str] = mapped_column(String(100), default="Main batch")
    egg_count: Mapped[int] = mapped_column(Integer, default=0)
    loading_date: Mapped[date] = mapped_column(Date)
    incubation_days: Mapped[int] = mapped_column(Integer, default=21)
    lockdown_day: Mapped[int] = mapped_column(Integer, default=18)
    target_temperature: Mapped[float] = mapped_column(Float, default=37.5)
    target_humidity: Mapped[float] = mapped_column(Float, default=60.0)
    turning_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    turning_disabled_day: Mapped[int] = mapped_column(Integer, default=18)
    notes: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)


class ServoHistory(Base):
    __tablename__ = "servo_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    profile_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(40), default="cycle", index=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    target_angle: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    message: Mapped[str] = mapped_column(String(240), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)


class HeaterHistory(Base):
    __tablename__ = "heater_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    relay_event_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)


class PowerConfig(Base):
    __tablename__ = "power_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    heater_watts: Mapped[float] = mapped_column(Float, default=60.0)
    fan_watts: Mapped[float] = mapped_column(Float, default=3.0)
    controller_watts: Mapped[float] = mapped_column(Float, default=1.0)
    servo_watts: Mapped[float] = mapped_column(Float, default=5.0)
    servo_average_watts: Mapped[float] = mapped_column(Float, default=0.1)
    lcd_watts: Mapped[float] = mapped_column(Float, default=0.5)
    relay_watts: Mapped[float] = mapped_column(Float, default=0.4)
    dht22_watts: Mapped[float] = mapped_column(Float, default=0.02)
    buzzer_watts: Mapped[float] = mapped_column(Float, default=0.0)
    grid_voltage: Mapped[float] = mapped_column(Float, default=220.0)
    tariff_per_kwh: Mapped[float] = mapped_column(Float, default=0.0)
    battery_backup_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    battery_voltage: Mapped[float] = mapped_column(Float, default=12.0)
    battery_capacity_ah: Mapped[float] = mapped_column(Float, default=100.0)
    battery_charge_percent: Mapped[float] = mapped_column(Float, default=100.0)
    battery_health_percent: Mapped[float] = mapped_column(Float, default=100.0)
    battery_usable_percent: Mapped[float] = mapped_column(Float, default=60.0)
    inverter_efficiency_percent: Mapped[float] = mapped_column(Float, default=88.0)
    battery_chemistry: Mapped[str] = mapped_column(String(40), default="Lead Acid")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)


class PowerHistory(Base):
    __tablename__ = "power_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    metric: Mapped[str] = mapped_column(String(60), index=True)
    value: Mapped[float] = mapped_column(Float, default=0.0)
    unit: Mapped[str] = mapped_column(String(20), default="")
    payload: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)


class AlarmHistory(Base):
    __tablename__ = "alarm_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    module: Mapped[str] = mapped_column(String(60), index=True)
    severity: Mapped[str] = mapped_column(String(20), default="warning")
    message: Mapped[str] = mapped_column(String(240))
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    muted: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)


class HealthHistory(Base):
    __tablename__ = "health_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    module: Mapped[str] = mapped_column(String(60), index=True)
    state: Mapped[str] = mapped_column(String(30), default="ok", index=True)
    detail: Mapped[str] = mapped_column(String(240), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)

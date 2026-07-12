from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

RelayMode = Literal["AUTO", "MANUAL", "EMERGENCY_OFF"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EnvironmentIn(BaseModel):
    temperature: float = Field(ge=0, le=80)
    humidity: float = Field(ge=0, le=100)
    heat_index: float | None = Field(default=None, ge=0, le=90)
    relay: bool = False
    fan_relay: bool = False
    wifi: bool = True
    sync_status: str = "synced"
    fault_code: str | None = Field(default=None, max_length=60)
    fault_title: str | None = Field(default=None, max_length=80)
    fault_detail: str | None = Field(default=None, max_length=160)
    timestamp: datetime = Field(default_factory=utc_now)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_payload(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        if "sync_status" not in payload and "syncStatus" in payload:
            payload["sync_status"] = payload.pop("syncStatus")
        if payload.get("timestamp") in ("", None):
            payload.pop("timestamp", None)
        return payload


class EnvironmentOut(EnvironmentIn):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SettingsIn(BaseModel):
    device_name: str | None = Field(default=None, min_length=1, max_length=80)
    timezone: str | None = Field(default=None, min_length=1, max_length=80)
    target_temperature: float | None = Field(default=None, ge=20, le=45)
    target_humidity: float | None = Field(default=None, ge=20, le=95)
    tolerance: float | None = Field(default=None, ge=0.1, le=5)
    hysteresis: float | None = Field(default=None, ge=0.05, le=3)
    sampling_interval: int | None = Field(default=None, ge=1, le=3600)
    sync_interval: int | None = Field(default=None, ge=1, le=3600)
    temperature_offset: float | None = Field(default=None, ge=-10, le=10)
    humidity_offset: float | None = Field(default=None, ge=-25, le=25)
    relay_mode: RelayMode | None = None
    manual_relay: bool | None = None
    emergency_off: bool | None = None
    tray_servo_enabled: bool | None = None
    tray_servo_angle: int | None = Field(default=None, ge=0, le=180)
    tray_servo_interval_minutes: int | None = Field(default=None, ge=1, le=720)
    tray_servo_speed_dps: int | None = Field(default=None, ge=1, le=30)
    wifi_ssid: str | None = Field(default=None, max_length=80)
    wifi_password: str | None = Field(default=None, max_length=128)
    wifi_scan_requested: bool | None = None
    wifi_connect_requested: bool | None = None
    timestamp: datetime = Field(default_factory=utc_now)

    @field_validator("relay_mode", mode="before")
    @classmethod
    def normalize_relay_mode(cls, value: str | None) -> str | None:
        return value.upper() if isinstance(value, str) else value


class SettingsOut(BaseModel):
    id: int
    device_name: str
    timezone: str
    target_temperature: float
    target_humidity: float
    tolerance: float
    hysteresis: float
    sampling_interval: int
    sync_interval: int
    temperature_offset: float
    humidity_offset: float
    relay_mode: str
    manual_relay: bool
    emergency_off: bool
    tray_servo_enabled: bool
    tray_servo_angle: int
    tray_servo_interval_minutes: int
    tray_servo_speed_dps: int
    wifi_ssid: str | None
    wifi_password_set: bool
    wifi_scan_requested: bool
    wifi_connect_requested: bool
    wifi_active_ssid: str | None
    wifi_ip_address: str | None
    wifi_rssi: int | None
    wifi_connection_status: str
    wifi_last_scan_at: datetime | None
    wifi_last_connect_at: datetime | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RelayCommand(BaseModel):
    mode: RelayMode
    relay: bool = False
    reason: str = Field(default="operator command", max_length=160)
    timestamp: datetime = Field(default_factory=utc_now)

    @field_validator("mode", mode="before")
    @classmethod
    def normalize_mode(cls, value: str) -> str:
        return value.upper()


class CalibrationIn(BaseModel):
    temperature_offset: float = Field(ge=-10, le=10)
    humidity_offset: float = Field(ge=-25, le=25)


class AlertOut(BaseModel):
    id: int
    type: str
    severity: str
    message: str
    acknowledged: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertDeleteIn(BaseModel):
    ids: list[int] = Field(default_factory=list)


class NotificationSettingsIn(BaseModel):
    telegram_enabled: bool = False
    telegram_bot_token: str | None = Field(default=None, max_length=240)
    telegram_chat_id: str | None = Field(default=None, max_length=120)
    email_enabled: bool = False
    email_to: str | None = Field(default=None, max_length=160)
    email_from: str | None = Field(default=None, max_length=160)
    smtp_host: str | None = Field(default=None, max_length=160)
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = Field(default=None, max_length=160)
    smtp_password: str | None = Field(default=None, max_length=240)
    smtp_use_tls: bool = True


class NotificationSettingsOut(BaseModel):
    telegram_enabled: bool
    telegram_chat_id: str
    telegram_bot_token_set: bool
    email_enabled: bool
    email_to: str
    email_from: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password_set: bool
    smtp_use_tls: bool


class HistoryFilter(BaseModel):
    range: Literal["today", "week", "month", "custom"] = "today"
    start: datetime | None = None
    end: datetime | None = None


class ApiMessage(BaseModel):
    ok: bool = True
    message: str


class WifiConnectIn(BaseModel):
    ssid: str = Field(min_length=1, max_length=80)
    password: str = Field(default="", max_length=128)
    timestamp: datetime = Field(default_factory=utc_now)


class WifiNetworkIn(BaseModel):
    ssid: str = Field(min_length=1, max_length=80)
    rssi: int = 0
    encryption: str = Field(default="unknown", max_length=40)
    channel: int | None = None


class WifiNetworksIn(BaseModel):
    networks: list[WifiNetworkIn] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=utc_now)


class WifiNetworkOut(WifiNetworkIn):
    id: int
    last_seen_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WifiStatusIn(BaseModel):
    connected: bool = False
    ssid: str | None = Field(default=None, max_length=80)
    ip_address: str | None = Field(default=None, max_length=45)
    rssi: int | None = None
    status: str = Field(default="unknown", max_length=40)
    timestamp: datetime = Field(default_factory=utc_now)

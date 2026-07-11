from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


BirdCategory = Literal["chicken", "duck", "quail", "turkey", "goose", "custom"]


class IncubationProfileIn(BaseModel):
    bird_category: BirdCategory = "chicken"
    custom_bird: str | None = Field(default=None, max_length=80)
    batch_name: str = Field(default="Main batch", min_length=1, max_length=100)
    egg_count: int = Field(default=0, ge=0, le=10000)
    loading_date: date = Field(default_factory=date.today)
    incubation_days: int | None = Field(default=None, ge=1, le=120)
    lockdown_day: int | None = Field(default=None, ge=1, le=120)
    target_temperature: float | None = Field(default=None, ge=20, le=45)
    target_humidity: float | None = Field(default=None, ge=20, le=95)
    turning_enabled: bool = True
    turning_disabled_day: int | None = Field(default=None, ge=1, le=120)
    notes: str = Field(default="", max_length=2000)
    is_active: bool = True

    @field_validator("bird_category", mode="before")
    @classmethod
    def normalize_bird(cls, value: str) -> str:
        return value.strip().lower() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_turning_days(self) -> "IncubationProfileIn":
        days = self.incubation_days or 21
        lockdown = self.lockdown_day or max(1, days - 3)
        turning_disabled = self.turning_disabled_day or lockdown
        if lockdown > days:
            raise ValueError("lockdown_day cannot be greater than incubation_days")
        if turning_disabled > days:
            raise ValueError("turning_disabled_day cannot be greater than incubation_days")
        return self


class IncubationProfilePatch(BaseModel):
    bird_category: BirdCategory | None = None
    custom_bird: str | None = Field(default=None, max_length=80)
    batch_name: str | None = Field(default=None, min_length=1, max_length=100)
    egg_count: int | None = Field(default=None, ge=0, le=10000)
    loading_date: date | None = None
    incubation_days: int | None = Field(default=None, ge=1, le=120)
    lockdown_day: int | None = Field(default=None, ge=1, le=120)
    target_temperature: float | None = Field(default=None, ge=20, le=45)
    target_humidity: float | None = Field(default=None, ge=20, le=95)
    turning_enabled: bool | None = None
    turning_disabled_day: int | None = Field(default=None, ge=1, le=120)
    notes: str | None = Field(default=None, max_length=2000)
    is_active: bool | None = None

    @field_validator("bird_category", mode="before")
    @classmethod
    def normalize_bird(cls, value: str | None) -> str | None:
        return value.strip().lower() if isinstance(value, str) else value


class IncubationProfileOut(BaseModel):
    id: int
    bird_category: str
    custom_bird: str | None
    batch_name: str
    egg_count: int
    loading_date: date
    incubation_days: int
    lockdown_day: int
    target_temperature: float
    target_humidity: float
    turning_enabled: bool
    turning_disabled_day: int
    notes: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    current_day: int
    days_remaining: int
    progress_percent: float
    expected_hatch_date: date
    lockdown_date: date
    turning_enabled_today: bool

    model_config = ConfigDict(from_attributes=True)


class ServoEventIn(BaseModel):
    event_type: str = Field(default="cycle", max_length=40)
    success: bool = True
    target_angle: int = Field(default=0, ge=-180, le=180)
    duration_seconds: float = Field(default=0, ge=0, le=3600)
    message: str = Field(default="", max_length=240)


class PowerConfigIn(BaseModel):
    heater_watts: float = Field(ge=0, le=5000)
    fan_watts: float = Field(ge=0, le=500)
    controller_watts: float = Field(ge=0, le=500)
    servo_watts: float = Field(ge=0, le=500)
    grid_voltage: float = Field(ge=1, le=500)
    tariff_per_kwh: float = Field(ge=0, le=100000)


class AlarmPatch(BaseModel):
    resolved: bool | None = None
    muted: bool | None = None


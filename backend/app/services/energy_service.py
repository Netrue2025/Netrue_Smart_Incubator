from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.entities import PowerConfig, SensorReading, ServoHistory
from app.services.duty_cycle_service import DutyCycleService
from app.utils.time import ensure_aware_utc


class EnergyService:
    @staticmethod
    def base_average_watts(config: PowerConfig) -> float:
        return (
            config.fan_watts
            + config.controller_watts
            + config.lcd_watts
            + config.relay_watts
            + config.servo_average_watts
            + config.dht22_watts
            + config.buzzer_watts
        )

    @staticmethod
    def average_load_from_duty(config: PowerConfig, duty_percent: float) -> dict[str, float]:
        heater_average = config.heater_watts * (duty_percent / 100)
        base_average = EnergyService.base_average_watts(config)
        total_average = heater_average + base_average
        return {
            "heater_average_watts": heater_average,
            "base_average_watts": base_average,
            "average_watts": total_average,
        }

    @staticmethod
    def servo_active(db: Session, at_time: datetime | None = None) -> bool:
        now = ensure_aware_utc(at_time or datetime.now(timezone.utc))
        latest = db.scalars(select(ServoHistory).order_by(desc(ServoHistory.created_at)).limit(1)).first()
        if not latest or latest.duration_seconds <= 0:
            return False
        started = ensure_aware_utc(latest.created_at)
        return 0 <= (now - started).total_seconds() <= latest.duration_seconds

    @staticmethod
    def live_load_watts(config: PowerConfig, reading: SensorReading | None, servo_active: bool = False, buzzer_active: bool = False) -> float:
        heater_on = bool(reading and reading.relay)
        fan_on = bool(reading and reading.fan_relay)
        watts = config.controller_watts + config.lcd_watts + config.dht22_watts
        watts += config.heater_watts if heater_on else 0.0
        watts += config.relay_watts if heater_on else 0.0
        watts += config.fan_watts if fan_on else 0.0
        watts += config.servo_watts if servo_active else 0.0
        watts += config.buzzer_watts if buzzer_active else 0.0
        return watts

    @staticmethod
    def energy_window(db: Session, config: PowerConfig, begin: datetime, finish: datetime) -> dict[str, Any]:
        begin = ensure_aware_utc(begin)
        finish = ensure_aware_utc(finish)
        window_seconds = max(0.0, (finish - begin).total_seconds())
        duty = DutyCycleService.relay_runtime(db, begin, finish)
        duty_percent = min(100.0, max(0.0, (duty["seconds"] / max(1.0, window_seconds)) * 100))
        load = EnergyService.average_load_from_duty(config, duty_percent)
        wh = load["average_watts"] * (window_seconds / 3600)
        return {
            "wh": wh,
            "average_watts": load["average_watts"],
            "peak_watts": config.heater_watts + load["base_average_watts"],
            "readings": [],
            "sample_count": len(duty["events"]),
            "coverage_seconds": window_seconds,
            "heater_on_seconds": duty["seconds"],
            "heater_duty_percent": duty_percent,
            "heater_average_watts": load["heater_average_watts"],
            "base_average_watts": load["base_average_watts"],
        }

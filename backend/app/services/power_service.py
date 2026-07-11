from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.entities import PowerConfig, RelayEvent, SensorReading
from app.services.battery_service import BatteryService
from app.services.duty_cycle_service import DutyCycleService
from app.services.energy_service import EnergyService
from app.services.history_service import HistoryService
from app.services.incubator import get_or_create_settings, latest_reading
from app.services.pdf_service import PDFService
from app.utils.time import ensure_aware_utc


class PowerService:
    @staticmethod
    def normalize_legacy_defaults(db: Session, config: PowerConfig) -> PowerConfig:
        changed = False
        if config.fan_watts == 2.5:
            config.fan_watts = 3.0
            changed = True
        if config.controller_watts == 3.0:
            config.controller_watts = 1.0
            changed = True
        if config.servo_average_watts == 0.0:
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

    @staticmethod
    def config_payload(config: PowerConfig) -> dict[str, Any]:
        return {
            "heater_watts": config.heater_watts,
            "fan_watts": config.fan_watts,
            "controller_watts": config.controller_watts,
            "servo_watts": config.servo_watts,
            "servo_average_watts": config.servo_average_watts,
            "lcd_watts": config.lcd_watts,
            "relay_watts": config.relay_watts,
            "dht22_watts": config.dht22_watts,
            "buzzer_watts": config.buzzer_watts,
            "grid_voltage": config.grid_voltage,
            "tariff_per_kwh": config.tariff_per_kwh,
            "battery_backup_enabled": config.battery_backup_enabled,
            "battery_voltage": config.battery_voltage,
            "battery_capacity_ah": config.battery_capacity_ah,
            "battery_charge_percent": config.battery_charge_percent,
            "battery_health_percent": config.battery_health_percent,
            "battery_usable_percent": config.battery_usable_percent,
            "inverter_efficiency_percent": config.inverter_efficiency_percent,
            "battery_chemistry": config.battery_chemistry,
            "updated_at": config.updated_at,
        }

    @staticmethod
    def latest_relay_times(db: Session) -> dict[str, Any]:
        on_event = db.scalars(select(RelayEvent).where(RelayEvent.relay.is_(True)).order_by(desc(RelayEvent.created_at)).limit(1)).first()
        off_event = db.scalars(select(RelayEvent).where(RelayEvent.relay.is_(False)).order_by(desc(RelayEvent.created_at)).limit(1)).first()
        return {"heater_on_time": on_event.created_at if on_event else None, "heater_off_time": off_event.created_at if off_event else None}

    @staticmethod
    def buzzer_active(db: Session) -> bool:
        return False

    @staticmethod
    def summary(db: Session, log: bool = True) -> dict[str, Any]:
        from app.services.logger_service import LoggerService

        config = db.get(PowerConfig, 1)
        if not config:
            config = PowerConfig(id=1)
            db.add(config)
            db.commit()
            db.refresh(config)
        config = PowerService.normalize_legacy_defaults(db, config)

        now = ensure_aware_utc(datetime.now(timezone.utc))
        current_hour_begin = now.replace(minute=0, second=0, microsecond=0)
        last_completed_hour_begin = current_hour_begin - timedelta(hours=1)
        day_begin = now.replace(hour=0, minute=0, second=0, microsecond=0)
        reading = latest_reading(db)
        settings = get_or_create_settings(db)
        servo_active = EnergyService.servo_active(db, now)
        buzzer_active = PowerService.buzzer_active(db)
        live_load = EnergyService.live_load_watts(config, reading, servo_active, buzzer_active)
        last_hour_energy = EnergyService.energy_window(db, config, last_completed_hour_begin, current_hour_begin)
        current_hour_energy = EnergyService.energy_window(db, config, current_hour_begin, now)
        today_energy = EnergyService.energy_window(db, config, day_begin, now)
        duty = DutyCycleService.relay_runtime(db, last_completed_hour_begin, current_hour_begin)
        last_hour_duty_percent = round(last_hour_energy["heater_duty_percent"], 1)
        runtime_basis_watts = last_hour_energy["average_watts"] or current_hour_energy["average_watts"]
        battery = BatteryService.remaining(config, max(0.01, runtime_basis_watts), now)
        battery["basis_average_watts"] = round(runtime_basis_watts, 2)
        battery["sample_count"] = last_hour_energy["sample_count"]
        battery["confidence"] = "low" if last_hour_energy["sample_count"] < 5 else "ok"
        relay_times = PowerService.latest_relay_times(db)
        total_kwh = today_energy["wh"] / 1000
        estimated_current = live_load / max(1, config.grid_voltage)
        hourly_history = HistoryService.hourly_points(db, config, 24)
        payload = {
            "config": PowerService.config_payload(config),
            "window_hours": 24,
            "heater_kwh": round((config.heater_watts * duty["seconds"]) / 3600000, 4),
            "base_kwh": round(today_energy["wh"] / 1000, 4),
            "servo_kwh": 0.0,
            "total_kwh": round(total_kwh, 4),
            "estimated_cost": round(total_kwh * config.tariff_per_kwh, 2),
            "estimated_current_amps": round(estimated_current, 3),
            "heater_runtime_minutes": round(duty["seconds"] / 60, 1),
            "heater_cycles": duty["cycles"],
            "live_load_watts": round(live_load, 2),
            "average_load_watts": round(last_hour_energy["average_watts"], 2),
            "peak_load_watts": round(max(today_energy["peak_watts"], live_load), 2),
            "energy_last_hour_wh": round(last_hour_energy["wh"], 2),
            "energy_current_hour_wh": round(current_hour_energy["wh"], 2),
            "energy_today_wh": round(today_energy["wh"], 2),
            "heater_duty_last_hour_percent": last_hour_duty_percent,
            "heater_duty_current_hour_percent": round(current_hour_energy["heater_duty_percent"], 1),
            "last_completed_hour_start": last_completed_hour_begin,
            "last_completed_hour_end": current_hour_begin,
            "last_completed_hour_label": f"{last_completed_hour_begin.strftime('%H:00')} - {current_hour_begin.strftime('%H:00')} GMT",
            "current_hour_start": current_hour_begin,
            "current_hour_label": f"{current_hour_begin.strftime('%H:00')} - {(current_hour_begin + timedelta(hours=1)).strftime('%H:00')} GMT",
            "rtc_time": now,
            "battery": battery,
            "recharge_before": battery["recharge_before"],
            "live": {
                "heater_state": "ON" if reading and reading.relay else "OFF",
                "heater_on": bool(reading and reading.relay),
                "heater_on_time": relay_times["heater_on_time"],
                "heater_off_time": relay_times["heater_off_time"],
                "temperature": reading.temperature if reading else None,
                "humidity": reading.humidity if reading else None,
                "fan_on": bool(reading and reading.fan_relay),
                "servo_status": "Moving" if servo_active else ("Enabled" if settings.tray_servo_enabled else "Stopped"),
                "servo_active": servo_active,
                "buzzer_active": buzzer_active,
            },
            "hourly_history": hourly_history,
        }
        payload["report"] = PDFService.report_payload(payload)
        if log:
            LoggerService.maybe_log_power(db)
        return payload

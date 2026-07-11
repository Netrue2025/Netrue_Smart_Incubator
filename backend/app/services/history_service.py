import json
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.entities import PowerConfig, PowerHistory
from app.services.duty_cycle_service import DutyCycleService
from app.services.energy_service import EnergyService
from app.utils.time import ensure_aware_utc


class HistoryService:
    @staticmethod
    def power_history_rows(db: Session, limit: int = 100) -> list[dict[str, Any]]:
        rows = db.scalars(select(PowerHistory).order_by(desc(PowerHistory.created_at)).limit(limit)).all()
        return [
            {
                "id": row.id,
                "metric": row.metric,
                "value": row.value,
                "unit": row.unit,
                "payload": row.payload,
                "created_at": row.created_at,
            }
            for row in rows
        ]

    @staticmethod
    def hourly_points(db: Session, config: PowerConfig, hours: int = 24) -> list[dict[str, Any]]:
        now = ensure_aware_utc(datetime.now(timezone.utc))
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        points: list[dict[str, Any]] = []
        for hour in range(24):
            begin = day_start + timedelta(hours=hour)
            stop = begin + timedelta(hours=1)
            if begin > now:
                energy = {"wh": 0.0, "average_watts": 0.0, "heater_duty_percent": 0.0}
                duty = 0.0
            else:
                effective_stop = min(stop, now)
                closed_hour_log = None
                if stop <= now:
                    closed_hour_log = db.scalars(
                        select(PowerHistory)
                        .where(PowerHistory.metric == "ems_hour", PowerHistory.created_at >= begin, PowerHistory.created_at < stop)
                        .order_by(desc(PowerHistory.created_at))
                        .limit(1)
                    ).first()
                logged_payload: dict[str, Any] = {}
                if closed_hour_log and closed_hour_log.payload:
                    with suppress(json.JSONDecodeError):
                        logged_payload = json.loads(closed_hour_log.payload)
                if closed_hour_log and logged_payload.get("hour_end"):
                    energy = {
                        "wh": closed_hour_log.value,
                        "average_watts": float(logged_payload.get("average_load_watts") or 0.0),
                        "heater_duty_percent": float(logged_payload.get("average_heater_duty_percent") or 0.0),
                    }
                    duty = energy["heater_duty_percent"]
                else:
                    energy = EnergyService.energy_window(db, config, begin, effective_stop)
                    duty = DutyCycleService.duty_percent(db, begin, effective_stop)
            latest_log = db.scalars(
                select(PowerHistory)
                .where(PowerHistory.metric == "ems_minute", PowerHistory.created_at >= begin, PowerHistory.created_at < stop)
                .order_by(desc(PowerHistory.created_at))
                .limit(1)
            ).first()
            battery_percent = None
            if latest_log and latest_log.payload:
                with suppress(json.JSONDecodeError):
                    battery_percent = json.loads(latest_log.payload).get("battery_percent")
            points.append(
                {
                    "hour": begin.strftime("%H:00"),
                    "created_at": begin,
                    "energy_wh": round(energy["wh"], 2),
                    "average_load_watts": round(energy["average_watts"], 2),
                    "heater_duty_percent": round(duty, 1),
                    "battery_percent": battery_percent if battery_percent is not None else round(config.battery_charge_percent, 1),
                }
            )
        return points

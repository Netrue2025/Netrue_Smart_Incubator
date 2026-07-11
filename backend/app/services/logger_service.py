import json
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.entities import PowerHistory
from app.services.power_service import PowerService
from app.utils.time import ensure_aware_utc


class LoggerService:
    @staticmethod
    def maybe_log_power(db: Session) -> None:
        now = ensure_aware_utc(datetime.now(timezone.utc))
        latest_minute = db.scalars(
            select(PowerHistory)
            .where(PowerHistory.metric == "ems_minute")
            .order_by(desc(PowerHistory.created_at))
            .limit(1)
        ).first()
        if latest_minute and (now - ensure_aware_utc(latest_minute.created_at)).total_seconds() < 60:
            return

        summary = PowerService.summary(db, log=False)
        minute_payload = {
            "timestamp": now.isoformat(),
            "current_load_watts": summary["live_load_watts"],
            "average_load_watts": summary["average_load_watts"],
            "heater_duty_percent": summary["heater_duty_last_hour_percent"],
            "battery_percent": summary["config"]["battery_charge_percent"],
            "temperature": summary["live"]["temperature"],
            "humidity": summary["live"]["humidity"],
            "servo_status": summary["live"]["servo_status"],
            "heater_status": summary["live"]["heater_state"],
            "energy_consumed_wh": summary["energy_today_wh"],
        }
        db.add(PowerHistory(metric="ems_minute", value=summary["live_load_watts"], unit="W", payload=json.dumps(minute_payload)))

        latest_hour = db.scalars(
            select(PowerHistory)
            .where(
                PowerHistory.metric == "ems_hour",
                PowerHistory.created_at >= summary["last_completed_hour_start"],
                PowerHistory.created_at < summary["last_completed_hour_end"],
            )
            .order_by(desc(PowerHistory.created_at))
            .limit(1)
        ).first()
        if latest_hour is None:
            hourly_payload = {
                "hour": summary["last_completed_hour_start"].isoformat(),
                "hour_end": summary["last_completed_hour_end"].isoformat(),
                "average_load_watts": summary["average_load_watts"],
                "average_heater_duty_percent": summary["heater_duty_last_hour_percent"],
                "hourly_energy_wh": summary["energy_last_hour_wh"],
                "battery_percent": summary["config"]["battery_charge_percent"],
            }
            db.add(
                PowerHistory(
                    metric="ems_hour",
                    value=summary["energy_last_hour_wh"],
                    unit="Wh",
                    payload=json.dumps(hourly_payload),
                    created_at=summary["last_completed_hour_start"],
                )
            )
        db.commit()

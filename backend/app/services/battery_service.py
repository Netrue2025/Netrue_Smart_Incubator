from datetime import datetime, timedelta, timezone
from typing import Any

from app.models.entities import PowerConfig
from app.utils.time import ensure_aware_utc


class BatteryService:
    @staticmethod
    def remaining(config: PowerConfig, average_watts: float, now: datetime | None = None) -> dict[str, Any]:
        current = ensure_aware_utc(now or datetime.now(timezone.utc))
        usable_wh = (
            config.battery_voltage
            * config.battery_capacity_ah
            * (config.battery_charge_percent / 100)
            * (config.battery_health_percent / 100)
            * (config.battery_usable_percent / 100)
            * (config.inverter_efficiency_percent / 100)
        )
        runtime_hours = usable_wh / average_watts if average_watts > 0 else None
        recharge_at = current + timedelta(hours=runtime_hours) if runtime_hours is not None else None
        if runtime_hours is None:
            severity = "unknown"
        elif runtime_hours < 4:
            severity = "critical"
        elif runtime_hours < 8:
            severity = "warning"
        else:
            severity = "ok"
        return {
            "energy_wh": round(usable_wh, 1),
            "runtime_hours": round(runtime_hours, 2) if runtime_hours is not None else None,
            "recharge_before": recharge_at,
            "severity": severity,
        }

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.entities import RelayEvent
from app.utils.time import ensure_aware_utc


class DutyCycleService:
    @staticmethod
    def relay_runtime(db: Session, begin: datetime, finish: datetime) -> dict[str, Any]:
        begin = ensure_aware_utc(begin)
        finish = ensure_aware_utc(finish)
        previous = db.scalars(
            select(RelayEvent)
            .where(RelayEvent.created_at < begin)
            .order_by(desc(RelayEvent.created_at))
            .limit(1)
        ).first()
        events = db.scalars(
            select(RelayEvent)
            .where(RelayEvent.created_at >= begin, RelayEvent.created_at <= finish)
            .order_by(RelayEvent.created_at)
        ).all()

        total_seconds = 0.0
        cycles = 0
        on_at: datetime | None = begin if previous and previous.relay else None
        for event in events:
            event_time = ensure_aware_utc(event.created_at)
            if event.relay and on_at is None:
                on_at = event_time
                cycles += 1
            elif not event.relay and on_at is not None:
                total_seconds += max(0.0, (event_time - on_at).total_seconds())
                on_at = None
        if on_at is not None:
            total_seconds += max(0.0, (finish - on_at).total_seconds())

        return {"seconds": total_seconds, "cycles": cycles, "events": events, "currently_on": on_at is not None}

    @staticmethod
    def duty_percent(db: Session, begin: datetime, finish: datetime) -> float:
        window_seconds = max(1.0, (ensure_aware_utc(finish) - ensure_aware_utc(begin)).total_seconds())
        runtime = DutyCycleService.relay_runtime(db, begin, finish)
        return min(100.0, max(0.0, (runtime["seconds"] / window_seconds) * 100))

    @staticmethod
    def rolling_hour(db: Session, finish: datetime | None = None) -> dict[str, Any]:
        stop = ensure_aware_utc(finish or datetime.now(timezone.utc))
        begin = stop - timedelta(hours=1)
        runtime = DutyCycleService.relay_runtime(db, begin, stop)
        return {
            "begin": begin,
            "finish": stop,
            "seconds": round(runtime["seconds"], 1),
            "cycles": runtime["cycles"],
            "currently_on": runtime["currently_on"],
            "percent": round((runtime["seconds"] / 3600) * 100, 1),
            "events": runtime["events"],
        }

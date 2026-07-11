import asyncio
from contextlib import suppress

from app.database.session import SessionLocal
from app.queue.offline_queue import pending_count
from app.services.incubator import create_alert, latest_reading, status_snapshot
from app.utils.time import ensure_aware_utc
from app.websocket.manager import manager


async def live_scheduler(stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        with SessionLocal() as db:
            snapshot = status_snapshot(db)
            reading = latest_reading(db)
            if reading:
                age = (ensure_aware_utc() - ensure_aware_utc(reading.created_at)).total_seconds()
                if age > 8:
                    create_alert(db, "sensor_disconnected", "critical", "No fresh DHT22 reading received")
            if pending_count(db) > 1000:
                create_alert(db, "storage_full", "critical", "Sync queue has grown beyond 1000 items")
            await manager.broadcast(snapshot)
        with suppress(asyncio.TimeoutError):
            await asyncio.wait_for(stop_event.wait(), timeout=1)

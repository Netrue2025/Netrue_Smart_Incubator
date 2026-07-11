import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import SyncQueueItem


def enqueue(db: Session, direction: str, topic: str, payload: dict[str, Any]) -> SyncQueueItem:
    item = SyncQueueItem(direction=direction, topic=topic, payload=json.dumps(payload, default=str))
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def pending_count(db: Session) -> int:
    return len(db.scalars(select(SyncQueueItem).where(SyncQueueItem.status == "pending")).all())


def mark_processed(db: Session, item: SyncQueueItem) -> None:
    item.status = "processed"
    item.processed_at = datetime.now(timezone.utc)
    db.add(item)
    db.commit()

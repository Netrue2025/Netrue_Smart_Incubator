from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import AnalyticsCache
from app.storage.provider import StorageProvider


class DatabaseStorage(StorageProvider):
    def __init__(self, db: Session):
        self.db = db

    def save(self, key: str, payload: str) -> None:
        item = self.db.scalars(select(AnalyticsCache).where(AnalyticsCache.cache_key == key).limit(1)).first()
        if item:
            item.payload = payload
        else:
            item = AnalyticsCache(cache_key=key, payload=payload)
        self.db.add(item)
        self.db.commit()

    def read(self, key: str) -> str | None:
        item = self.db.scalars(select(AnalyticsCache).where(AnalyticsCache.cache_key == key).limit(1)).first()
        return item.payload if item else None

    def delete(self, key: str) -> None:
        item = self.db.scalars(select(AnalyticsCache).where(AnalyticsCache.cache_key == key).limit(1)).first()
        if item:
            self.db.delete(item)
            self.db.commit()

    def exists(self, key: str) -> bool:
        return self.read(key) is not None

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any


class CacheProvider(ABC):
    @abstractmethod
    def get(self, key: str) -> Any | None:
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        raise NotImplementedError


class MemoryCache(CacheProvider):
    def __init__(self) -> None:
        self._items: dict[str, tuple[Any, datetime | None]] = {}

    def get(self, key: str) -> Any | None:
        item = self._items.get(key)
        if not item:
            return None
        value, expires_at = item
        if expires_at and expires_at <= datetime.now(timezone.utc):
            self.delete(key)
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        expires_at = None
        if ttl_seconds:
            from datetime import timedelta

            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        self._items[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        self._items.pop(key, None)

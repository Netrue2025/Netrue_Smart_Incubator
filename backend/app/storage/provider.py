from abc import ABC, abstractmethod


class StorageProvider(ABC):
    @abstractmethod
    def save(self, key: str, payload: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def read(self, key: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def exists(self, key: str) -> bool:
        raise NotImplementedError

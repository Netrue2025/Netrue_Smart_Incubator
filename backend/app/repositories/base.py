from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session


ModelT = TypeVar("ModelT")


class Repository(Generic[ModelT]):
    def __init__(self, db: Session, model: type[ModelT]):
        self.db = db
        self.model = model

    def get(self, item_id: int) -> ModelT | None:
        return self.db.get(self.model, item_id)

    def list(self, limit: int = 100) -> list[ModelT]:
        return list(self.db.scalars(select(self.model).limit(limit)).all())

    def add(self, item: ModelT) -> ModelT:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item: ModelT) -> None:
        self.db.delete(item)
        self.db.commit()

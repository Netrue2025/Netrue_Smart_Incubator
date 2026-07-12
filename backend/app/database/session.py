from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config.settings import get_settings


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    database_url = get_settings().database_url
    if not database_url:
        raise RuntimeError("Database is not configured. Set DATABASE_URL or DB_HOST, DB_NAME, DB_USER, and DB_PASSWORD.")
    if database_url.split(":", 1)[0].lower() == "sqlite":
        raise RuntimeError("Local file databases are not supported in cloud mode. Configure a MySQL DATABASE_URL.")
    return database_url


@lru_cache
def get_engine() -> Engine:
    return create_engine(
        get_database_url(),
        pool_pre_ping=True,
        pool_recycle=280,
        pool_size=5,
        max_overflow=5,
        future=True,
    )


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    from app.models import entities  # noqa: F401

    Base.metadata.create_all(bind=get_engine())


def get_db() -> Generator[Session, None, None]:
    db = get_sessionmaker()()
    try:
        yield db
    finally:
        db.close()

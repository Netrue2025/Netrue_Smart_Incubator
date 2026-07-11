from collections.abc import Generator

from sqlalchemy import inspect, text
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config.settings import get_settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    get_settings().database_url,
    connect_args={"check_same_thread": False},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    from app.models import entities  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_device_settings_columns()
    ensure_sensor_reading_columns()


def ensure_device_settings_columns() -> None:
    inspector = inspect(engine)
    if "device_settings" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("device_settings")}
    additions = {
        "tray_servo_enabled": "BOOLEAN NOT NULL DEFAULT 0",
        "tray_servo_angle": "INTEGER NOT NULL DEFAULT 45",
        "tray_servo_interval_minutes": "INTEGER NOT NULL DEFAULT 120",
        "tray_servo_speed_dps": "INTEGER NOT NULL DEFAULT 6",
    }
    with engine.begin() as connection:
        for name, definition in additions.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE device_settings ADD COLUMN {name} {definition}"))


def ensure_sensor_reading_columns() -> None:
    inspector = inspect(engine)
    if "sensor_readings" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("sensor_readings")}
    additions = {
        "fan_relay": "BOOLEAN NOT NULL DEFAULT 0",
    }
    with engine.begin() as connection:
        for name, definition in additions.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE sensor_readings ADD COLUMN {name} {definition}"))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from collections.abc import Generator

from sqlalchemy import inspect, text
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config.settings import get_settings


class Base(DeclarativeBase):
    pass


database_url = get_settings().database_url
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
engine = create_engine(database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    from app.models import entities  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_device_settings_columns()
    ensure_sensor_reading_columns()
    ensure_power_config_columns()


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
        "wifi_ssid": "VARCHAR(80)",
        "wifi_password": "VARCHAR(128)",
        "wifi_scan_requested": "BOOLEAN NOT NULL DEFAULT 0",
        "wifi_connect_requested": "BOOLEAN NOT NULL DEFAULT 0",
        "wifi_active_ssid": "VARCHAR(80)",
        "wifi_ip_address": "VARCHAR(45)",
        "wifi_rssi": "INTEGER",
        "wifi_connection_status": "VARCHAR(40) NOT NULL DEFAULT 'not_configured'",
        "wifi_last_scan_at": "DATETIME",
        "wifi_last_connect_at": "DATETIME",
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


def ensure_power_config_columns() -> None:
    inspector = inspect(engine)
    if "power_config" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("power_config")}
    additions = {
        "servo_average_watts": "FLOAT NOT NULL DEFAULT 0.1",
        "lcd_watts": "FLOAT NOT NULL DEFAULT 0.5",
        "relay_watts": "FLOAT NOT NULL DEFAULT 0.4",
        "dht22_watts": "FLOAT NOT NULL DEFAULT 0.02",
        "buzzer_watts": "FLOAT NOT NULL DEFAULT 0.0",
        "battery_backup_enabled": "BOOLEAN NOT NULL DEFAULT 0",
        "battery_voltage": "FLOAT NOT NULL DEFAULT 12.0",
        "battery_capacity_ah": "FLOAT NOT NULL DEFAULT 100.0",
        "battery_charge_percent": "FLOAT NOT NULL DEFAULT 100.0",
        "battery_health_percent": "FLOAT NOT NULL DEFAULT 100.0",
        "battery_usable_percent": "FLOAT NOT NULL DEFAULT 60.0",
        "inverter_efficiency_percent": "FLOAT NOT NULL DEFAULT 88.0",
        "battery_chemistry": "VARCHAR(40) NOT NULL DEFAULT 'Lead Acid'",
    }
    with engine.begin() as connection:
        for name, definition in additions.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE power_config ADD COLUMN {name} {definition}"))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

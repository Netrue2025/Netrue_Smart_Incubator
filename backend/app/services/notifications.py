import json
import smtplib
import ssl
import urllib.parse
import urllib.request
from email.message import EmailMessage
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Alert, AppSetting

SETTINGS_KEY = "alert_notifications"

DEFAULT_SETTINGS: dict[str, Any] = {
    "telegram_enabled": False,
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "email_enabled": False,
    "email_to": "",
    "email_from": "",
    "smtp_host": "",
    "smtp_port": 587,
    "smtp_username": "",
    "smtp_password": "",
    "smtp_use_tls": True,
}


def _settings_row(db: Session) -> AppSetting | None:
    return db.scalars(select(AppSetting).where(AppSetting.key == SETTINGS_KEY).limit(1)).first()


def get_notification_settings(db: Session, include_secrets: bool = False) -> dict[str, Any]:
    values = dict(DEFAULT_SETTINGS)
    row = _settings_row(db)
    if row and row.value:
        try:
            loaded = json.loads(row.value)
            if isinstance(loaded, dict):
                values.update(loaded)
        except json.JSONDecodeError:
            pass
    if include_secrets:
        return values
    return {
        "telegram_enabled": bool(values["telegram_enabled"]),
        "telegram_chat_id": values["telegram_chat_id"],
        "telegram_bot_token_set": bool(values["telegram_bot_token"]),
        "email_enabled": bool(values["email_enabled"]),
        "email_to": values["email_to"],
        "email_from": values["email_from"],
        "smtp_host": values["smtp_host"],
        "smtp_port": int(values["smtp_port"] or 587),
        "smtp_username": values["smtp_username"],
        "smtp_password_set": bool(values["smtp_password"]),
        "smtp_use_tls": bool(values["smtp_use_tls"]),
    }


def save_notification_settings(db: Session, payload: Any) -> dict[str, Any]:
    current = get_notification_settings(db, include_secrets=True)
    incoming = payload.model_dump()
    for key, value in incoming.items():
        if key in {"telegram_bot_token", "smtp_password"} and not value:
            continue
        current[key] = value if value is not None else ""
    current["smtp_port"] = int(current.get("smtp_port") or 587)

    row = _settings_row(db)
    if row is None:
        row = AppSetting(key=SETTINGS_KEY, category="notifications")
    row.value = json.dumps(current)
    db.add(row)
    db.commit()
    return get_notification_settings(db)


def notify_alert(db: Session, alert: Alert) -> None:
    settings = get_notification_settings(db, include_secrets=True)
    message = f"Smart Incubator Alert\nSeverity: {alert.severity}\nType: {alert.type}\nMessage: {alert.message}"
    if settings.get("telegram_enabled"):
        _send_telegram(settings, message)
    if settings.get("email_enabled"):
        _send_email(settings, f"Smart Incubator {alert.severity.title()} Alert", message)


def _send_telegram(settings: dict[str, Any], message: str) -> None:
    token = str(settings.get("telegram_bot_token") or "").strip()
    chat_id = str(settings.get("telegram_chat_id") or "").strip()
    if not token or not chat_id:
        return
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": message}).encode()
    request = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data, method="POST")
    with urllib.request.urlopen(request, timeout=8) as response:
        response.read()


def _send_email(settings: dict[str, Any], subject: str, body: str) -> None:
    host = str(settings.get("smtp_host") or "").strip()
    to_addr = str(settings.get("email_to") or "").strip()
    from_addr = str(settings.get("email_from") or settings.get("smtp_username") or "").strip()
    if not host or not to_addr or not from_addr:
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(body)

    port = int(settings.get("smtp_port") or 587)
    username = str(settings.get("smtp_username") or "").strip()
    password = str(settings.get("smtp_password") or "")
    if settings.get("smtp_use_tls"):
        with smtplib.SMTP(host, port, timeout=8) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            if username:
                smtp.login(username, password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP_SSL(host, port, timeout=8) as smtp:
            if username:
                smtp.login(username, password)
            smtp.send_message(msg)

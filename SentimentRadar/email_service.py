"""SMTP 邮件发送服务。"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from typing import Optional


def _settings():
    from config import reload_settings

    return reload_settings()


def _required(value: Optional[str], label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"请先配置 {label}")
    return text


def send_email(to_email: str, subject: str, text: str, html: Optional[str] = None) -> None:
    settings = _settings()
    if not settings.SMTP_ENABLED:
        raise ValueError("SMTP 未启用")

    host = _required(settings.SMTP_HOST, "SMTP_HOST")
    user = _required(settings.SMTP_USER, "SMTP_USER")
    password = _required(settings.SMTP_PASSWORD, "SMTP_PASSWORD")
    from_email = _required(settings.SMTP_FROM_EMAIL or settings.SMTP_USER, "SMTP_FROM_EMAIL")
    recipient = _required(to_email, "收件邮箱")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((settings.SMTP_FROM_NAME or "BettaFish", from_email))
    message["To"] = recipient
    message.set_content(text)
    if html:
        message.add_alternative(html, subtype="html")

    if settings.SMTP_USE_SSL:
        with smtplib.SMTP_SSL(host, int(settings.SMTP_PORT), timeout=15) as smtp:
            smtp.login(user, password)
            smtp.send_message(message)
    else:
        with smtplib.SMTP(host, int(settings.SMTP_PORT), timeout=15) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()
            smtp.login(user, password)
            smtp.send_message(message)


def send_test_email(to_email: str) -> None:
    send_email(
        to_email=to_email,
        subject="BettaFish 舆情雷达测试邮件",
        text="这是一封来自 BettaFish 舆情雷达的 SMTP 测试邮件。",
        html="<p>这是一封来自 <b>BettaFish 舆情雷达</b> 的 SMTP 测试邮件。</p>",
    )

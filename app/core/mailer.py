import asyncio
import smtplib
import ssl
import sys
from collections import deque
from datetime import UTC, datetime
from email.message import EmailMessage
from functools import lru_cache
from typing import Deque

from app.core.config import get_settings


class Mailer:
    """Adapter interface for sending emails."""

    async def send(self, to: str, subject: str, body: str) -> None:  # pragma: no cover - interface definition
        raise NotImplementedError


class ConsoleMailer(Mailer):
    """Mailer implementation that writes messages to stdout."""

    async def send(self, to: str, subject: str, body: str) -> None:
        message = (
            f"\n--- Console Mail ---\nTo: {to}\nSubject: {subject}\nBody:\n{body}\n--------------------\n"
        )
        print(message, file=sys.stdout)


class SMTPMailer(Mailer):
    """Mailer implementation backed by SMTP."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        from_email: str,
        use_tls: bool,
        use_ssl: bool,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_email = from_email
        self._use_tls = use_tls
        self._use_ssl = use_ssl

    async def send(self, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self._from_email
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        await asyncio.to_thread(self._send_sync, message)

    def _send_sync(self, message: EmailMessage) -> None:
        context = ssl.create_default_context()

        if self._use_ssl:
            smtp_class = smtplib.SMTP_SSL
        else:
            smtp_class = smtplib.SMTP

        with smtp_class(self._host, self._port, timeout=30) as server:
            if not self._use_ssl and self._use_tls:
                server.starttls(context=context)
            if self._username:
                server.login(self._username, self._password or "")
            server.send_message(message)


class MailProxy(Mailer):
    """Proxy that wraps a mailer with rate limiting, retries, and error suppression."""

    def __init__(
        self,
        mailer: Mailer,
        *,
        max_retries: int = 3,
        retry_delay: float = 0.5,
        min_interval: float = 0.5,
    ) -> None:
        self._mailer = mailer
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._min_interval = min_interval
        self._lock = asyncio.Lock()
        self._send_history: Deque[datetime] = deque(maxlen=10)

    async def send(self, to: str, subject: str, body: str) -> None:
        await self._throttle()

        attempt = 0
        while True:
            try:
                await self._mailer.send(to, subject, body)
                break
            except Exception as exc:  # pragma: no cover - best effort logging
                attempt += 1
                if attempt > self._max_retries:
                    print(f"[MailProxy] Failed to send email to {to}: {exc}", file=sys.stderr)
                    break
                await asyncio.sleep(self._retry_delay)

    async def _throttle(self) -> None:
        async with self._lock:
            now = datetime.now(UTC)
            if self._send_history:
                elapsed = (now - self._send_history[-1]).total_seconds()
                if elapsed < self._min_interval:
                    await asyncio.sleep(self._min_interval - elapsed)
            self._send_history.append(datetime.now(UTC))


@lru_cache
def get_mailer() -> Mailer:
    settings = get_settings()

    backend = settings.mailer_backend.lower().strip()
    if backend == "smtp":
        if not (settings.smtp_host and settings.smtp_port and settings.smtp_from_email):
            raise ValueError("SMTP backend selected but SMTP settings are incomplete")
        base_mailer = SMTPMailer(
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            from_email=settings.smtp_from_email,
            use_tls=settings.smtp_use_tls,
            use_ssl=settings.smtp_use_ssl,
        )
    else:
        base_mailer = ConsoleMailer()

    return MailProxy(
        base_mailer,
        max_retries=settings.mailer_max_retries,
        retry_delay=settings.mailer_retry_delay_seconds,
        min_interval=settings.mailer_rate_limit_seconds,
    )

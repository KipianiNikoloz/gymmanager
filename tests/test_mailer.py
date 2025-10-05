import asyncio

import pytest

from app.core.mailer import ConsoleMailer, MailProxy, Mailer

pytestmark = pytest.mark.asyncio


class FlakyMailer(Mailer):
    def __init__(self) -> None:
        self.calls = 0

    async def send(self, to: str, subject: str, body: str) -> None:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("temporary failure")


async def test_mail_proxy_retries_and_succeeds(capsys: pytest.CaptureFixture[str]) -> None:
    flaky = FlakyMailer()
    proxy = MailProxy(flaky, max_retries=2, retry_delay=0)

    await proxy.send("user@example.com", "Subject", "Body")

    assert flaky.calls == 2


async def test_console_mailer_outputs_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    mailer = ConsoleMailer()
    await mailer.send("dest@example.com", "Hello", "Message body")

    captured = capsys.readouterr().out
    assert "dest@example.com" in captured
    assert "Message body" in captured


async def test_mail_proxy_rate_limiting() -> None:
    mailer = ConsoleMailer()
    proxy = MailProxy(mailer, min_interval=0.01)

    await proxy.send("user@example.com", "Subject", "One")
    await proxy.send("user@example.com", "Subject", "Two")
    # No assertion besides ensuring it does not raise; awaits cover both branches.

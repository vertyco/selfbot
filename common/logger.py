import logging
from logging.handlers import RotatingFileHandler

import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.logging import LoggingIntegration


def init_logging(filename: str = "logs.log") -> logging.Logger:
    log = logging.getLogger("discord")
    log.setLevel(logging.DEBUG)
    logging.getLogger("discord.http").setLevel(logging.INFO)
    handler = RotatingFileHandler(
        filename=filename,
        mode="a",
        encoding="utf-8",
        maxBytes=1 * 1024 * 1024,  # 1 MiB
        backupCount=0,  # No backup files
    )
    dt_fmt = "%Y-%m-%d %I:%M:%S %p"
    formatter = logging.Formatter(
        "[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{"
    )
    handler.setFormatter(formatter)
    log.addHandler(handler)
    return log


def init_sentry(dsn: str) -> None:
    """Initializes Sentry SDK.

    Parameters
    ----------
    dsn: str
        The Sentry DSN to use.
    version: str
        The version of the application.
    """
    sentry_sdk.init(
        dsn=dsn,
        integrations=[
            AioHttpIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
        ignore_errors=[KeyboardInterrupt, RuntimeError],
    )

import logging
from logging.handlers import RotatingFileHandler

import sentry_sdk
from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

console = Console()


def grey(text):
    return Text(text, style="dim")


def blue(text):
    return Text(text, style="blue")


def green(text):
    return Text(text, style="green")


def yellow(text):
    return Text(text, style="yellow")


def red(text):
    return Text(text, style="red")


def crit(text):
    return Text(text, style="bold red on yellow")


class PrettyFormatter(logging.Formatter):
    formats = {
        logging.DEBUG: "[%(asctime)s] "
        + str(green("%(levelname)s    "))
        + str(grey("[%(name)s] "))
        + "%(message)s",
        logging.INFO: "[%(asctime)s] "
        + str(blue("%(levelname)s     "))
        + str(grey("[%(name)s] "))
        + "%(message)s",
        logging.WARNING: "[%(asctime)s] "
        + str(yellow("%(levelname)s  "))
        + str(grey("[%(name)s] "))
        + "%(message)s",
        logging.ERROR: "[%(asctime)s] "
        + str(red("%(levelname)s    "))
        + str(grey("[%(name)s] "))
        + "%(message)s",
        logging.CRITICAL: "[%(asctime)s] "
        + str(crit("%(levelname)s "))
        + str(grey("[%(name)s] "))
        + "%(message)s",
    }

    def format(self, record):
        log_fmt = self.formats.get(record.levelno)
        formatter = logging.Formatter(fmt=log_fmt, datefmt="%H:%M:%S")
        return formatter.format(record)


def init_logging(filename: str = "logs.log") -> None:
    print("Initializing logger")
    applogger = logging.getLogger("apscheduler")
    applogger.setLevel(logging.ERROR)

    # Console Log
    stdout_handler = RichHandler(console=console, rich_tracebacks=True)
    stdout_handler.setFormatter(PrettyFormatter())
    stdout_handler.setLevel(logging.INFO)

    handlers = [stdout_handler]

    datefmt = "%m-%d-%Y %I:%M:%S %p"
    logfmt = "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
    log_format = logging.Formatter(logfmt, datefmt=datefmt)

    # Info log
    info_file_handler = RotatingFileHandler(
        filename,
        mode="a",
        maxBytes=1 * 1024 * 1024,
        backupCount=0,
        encoding="utf-8",  # Ensure file handler uses UTF-8 encoding
    )
    info_file_handler.setFormatter(log_format)
    info_file_handler.setLevel(logging.INFO)

    handlers.append(info_file_handler)

    logging.basicConfig(
        level=logging.DEBUG,
        datefmt=datefmt,
        handlers=handlers,
    )


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

import logging
from logging.handlers import RotatingFileHandler

import colorama
import discord
import sentry_sdk
from colorama import Back, Fore, Style
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

green = Fore.LIGHTGREEN_EX + Style.BRIGHT
blue = Fore.LIGHTBLUE_EX + Style.BRIGHT
yellow = Fore.YELLOW + Style.BRIGHT
red = Fore.LIGHTRED_EX + Style.BRIGHT
critical = Fore.LIGHTYELLOW_EX + Back.RED + Style.BRIGHT
reset = Style.RESET_ALL + Fore.RESET + Back.RESET
timestring = Fore.LIGHTBLACK_EX + Style.BRIGHT + "%(asctime)s " + reset
name = Fore.MAGENTA + "%(name)s" + reset
formats = {
    logging.DEBUG: f"{timestring}{green}[ %(levelname)s  ]{reset} {name}: %(message)s",
    logging.INFO: f"{timestring}{blue}[  %(levelname)s  ]{reset} {name}: %(message)s",
    logging.WARNING: f"{timestring}{yellow}[%(levelname)s ]{reset} {name}: %(message)s",
    logging.ERROR: f"{timestring}{red}[ %(levelname)s  ]{reset} {name}: %(message)s",
    logging.CRITICAL: f"{timestring}{critical}[%(levelname)s]{reset} {name}: %(message)s",
}
dt_fmt = "%Y-%m-%d %I:%M:%S %p"
colorama.init(autoreset=True)


class PrettyFormatter(logging.Formatter):
    def format(self, record):
        log_fmt = formats[record.levelno]
        formatter = logging.Formatter(fmt=log_fmt, datefmt=dt_fmt)
        return formatter.format(record)


def init_logging(filename: str = "logs.log") -> logging.Logger:
    log = logging.getLogger("discord")
    handler = logging.StreamHandler()
    handler.setFormatter(PrettyFormatter())
    handler.setLevel(logging.DEBUG)
    log.addHandler(handler)

    logging.getLogger("discord.gateway").setLevel(logging.INFO)
    logging.getLogger("discord.client").setLevel(logging.INFO)
    logging.getLogger("discord.http").setLevel(logging.INFO)
    handler = RotatingFileHandler(
        filename=filename,
        mode="a",
        encoding="utf-8",
        maxBytes=1 * 1024 * 1024,  # 1 MiB
        backupCount=0,  # No backup files
    )
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
        ignore_errors=[KeyboardInterrupt, RuntimeError, discord.ConnectionClosed],
    )


if __name__ == "__main__":
    log = init_logging()
    log.debug("This is a debug message")
    log.info("This is an info message")
    log.warning("This is a warning message")
    log.error("This is an error message")
    log.critical("This is a critical message")

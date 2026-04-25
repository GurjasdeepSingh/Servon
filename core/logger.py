I = "info"
W = "warn"
E = "error"

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone, timedelta

# ===== CONFIG =====
LOG_DIR = "logs"
PER_GUILD_LOGS = False  # toggle this
MAX_BYTES = 5 * 1024 * 1024  # 5MB per file
BACKUP_COUNT = 3

IST = timezone(timedelta(hours=5, minutes=30))

os.makedirs(LOG_DIR, exist_ok=True)


class ISTFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, IST)
        return dt.strftime("%Y-%m-%d %H:%M:%S")


def _get_handler(filename: str):
    filepath = os.path.join(LOG_DIR, filename)

    handler = RotatingFileHandler(
        filepath,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )

    formatter = ISTFormatter(
        "[%(asctime)s] [%(levelname)s] [%(guild_id)s] [%(guild_name)s]: %(message)s"
    )
    handler.setFormatter(formatter)

    return handler


# cache loggers so we don’t recreate handlers repeatedly
_logger_cache = {}


def _get_logger(name: str, filename: str):
    if name in _logger_cache:
        return _logger_cache[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    handler = _get_handler(filename)
    logger.addHandler(handler)

    # console handler (shared format)
    console = logging.StreamHandler()
    console.setFormatter(handler.formatter)
    logger.addHandler(console)

    _logger_cache[name] = logger
    return logger


def log(message: str, level: str="info", guild=None):
    """
    level: 'I', 'W', 'E'
    guild: discord.Guild or None
    """

    level_map = {
        "info": logging.INFO,
        "warn": logging.WARNING,
        "error": logging.ERROR
    }

    log_level = level_map.get(level.upper(), logging.INFO)

    if guild:
        guild_id = guild.id
        guild_name = guild.name
    else:
        guild_id = "DEV"
        guild_name = "DEV"

    if PER_GUILD_LOGS and guild:
        filename = f"{guild_id}.log"
        logger_name = f"guild_{guild_id}"
    else:
        filename = "dev.log"
        logger_name = "global"

    logger = _get_logger(logger_name, filename)

    extra = {
        "guild_id": guild_id,
        "guild_name": guild_name
    }

    logger.log(log_level, message, extra=extra)


if __name__ == '__main__':
    class Guild:
        def __init__(self, name:str, id:int):
            self.name = name
            self.id = id
        def __bool__(self):
            return True
    myguild = Guild("Test GUild Name", 642983750242097)
    log("Hello test log 1234", E, myguild)
import richuru

from loguru import logger

from .data_file import get_data_path

LOGPATH = get_data_path("logs")
richuru.install(level="INFO")

logger.add(
    LOGPATH.joinpath("latest.log"),
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
    rotation="00:00",
    retention="1 week",
    compression="tar.xz",
    level="INFO",
)

logger.add(
    LOGPATH.joinpath("debug.log"),
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
    rotation="00:00",
    retention="3 days",
    compression="tar.xz",
    level="DEBUG",
)

logger.add(
    LOGPATH.joinpath("warning.log"),
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
    rotation="00:00",
    retention="3 days",
    compression="tar.xz",
    level="WARNING",
)

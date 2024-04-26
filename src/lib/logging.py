import logging
from .settings import APP_SETTINGS


LOGGING_LEVEL = APP_SETTINGS.logging_level  # DEBUG, INFO, WARNING, ERROR

if LOGGING_LEVEL is None:
    LOGGING_LEVEL = logging.INFO
elif LOGGING_LEVEL.upper() == "DEBUG":
    LOGGING_LEVEL = logging.DEBUG
elif LOGGING_LEVEL.upper() == "WARNING":
    LOGGING_LEVEL = logging.WARNING
elif LOGGING_LEVEL.upper() == "ERROR":
    LOGGING_LEVEL = logging.ERROR
else:
    LOGGING_LEVEL = logging.INFO


logging.basicConfig(  # basicConfig
    format="%(asctime)s [%(levelname)s] - [%(filename)s > %(funcName)s() > %(lineno)s] - %(message)s",
    level=LOGGING_LEVEL,
)

logger = logging.getLogger(__name__)

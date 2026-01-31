import logging
import sys
import uuid
from contextvars import ContextVar

from pythonjsonlogger import jsonlogger

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def setup_logging(debug: bool = False) -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s"
    )
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    logger.handlers = []
    logger.addHandler(handler)

    return logger


def generate_request_id() -> str:
    return str(uuid.uuid4())[:8]

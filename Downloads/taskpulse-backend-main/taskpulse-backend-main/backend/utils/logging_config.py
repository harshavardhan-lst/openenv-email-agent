"""Application logging setup (JSON-capable stream handler)."""

import json
import logging
import os
import sys
from typing import Optional


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "level": record.levelname,
            "time": self.formatTime(record, self.datefmt),
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, default=str)


def setup_logging(log_level: Optional[int] = None) -> None:
    level = log_level or int(os.getenv("LOG_LEVEL", logging.INFO))
    use_json = os.getenv("LOG_JSON", "0").lower() in ("1", "true", "yes")
    log_file = os.getenv("LOG_FILE", "").strip()

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    handler: logging.Handler = logging.StreamHandler(sys.stdout)
    if use_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
    root.addHandler(handler)

    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        root.addHandler(fh)

from datetime import datetime, timezone
import json
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
import sys
import traceback


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "@timestamp": datetime.now(timezone.utc).isoformat(),
            "log.level": record.levelname,
            "message": record.getMessage(),
            "service.name": "master-shop",
            "logger": record.name,
        }
        for key in ("event_action", "trace_id", "status_code", "duration_ms", "route"):
            if hasattr(record, key):
                payload[
                    {
                        "event_action": "event.action",
                        "trace_id": "trace.id",
                        "status_code": "http.response.status_code",
                        "duration_ms": "event.duration_ms",
                        "route": "http.route",
                    }[key]
                ] = getattr(record, key)
        if record.exc_info:
            payload["error.type"] = record.exc_info[0].__name__
            payload["error.stack_trace"] = "".join(traceback.format_list(traceback.extract_tb(record.exc_info[2])))
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(path):
    logger = logging.getLogger("shop")
    logger.setLevel(logging.DEBUG)
    for handler in logger.handlers:
        handler.close()
    logger.handlers.clear()
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(JsonFormatter())
    logger.addHandler(console)
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        file = TimedRotatingFileHandler(path, when="midnight", backupCount=14, encoding="utf-8")
        file.setFormatter(JsonFormatter())
        logger.addHandler(file)
    logger.propagate = False
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    return logger

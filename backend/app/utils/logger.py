import logging
import sys
from typing import Any

from app.config import settings


def setup_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_stage_event(stage: str, event: str, **kwargs: Any) -> None:
    logger = get_logger("pipeline.stage")
    extra = " | ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info("[%s] %s%s", stage, event, f" | {extra}" if extra else "")

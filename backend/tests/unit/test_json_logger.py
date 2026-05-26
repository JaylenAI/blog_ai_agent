from __future__ import annotations

import json
import logging
from unittest.mock import patch

import pytest


def test_json_formatter_output() -> None:
    from app.utils.logger import JsonFormatter

    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="테스트 메시지",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test.logger"
    assert parsed["message"] == "테스트 메시지"
    assert "timestamp" in parsed
    assert "exception" not in parsed


def test_json_formatter_with_exception() -> None:
    from app.utils.logger import JsonFormatter

    formatter = JsonFormatter()
    try:
        raise ValueError("테스트 에러")
    except ValueError:
        import sys

        record = logging.LogRecord(
            name="test.error",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="에러 발생",
            args=(),
            exc_info=sys.exc_info(),
        )

    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["level"] == "ERROR"
    assert "exception" in parsed
    assert "ValueError" in parsed["exception"]


def test_setup_logging_text_format() -> None:
    with patch("app.utils.logger.settings") as mock_settings:
        mock_settings.log_level = "INFO"
        mock_settings.log_format = "text"

        from app.utils.logger import setup_logging

        setup_logging()

    root = logging.getLogger()
    assert len(root.handlers) > 0
    handler = root.handlers[0]
    assert not isinstance(handler.formatter, type(None))


def test_setup_logging_json_format() -> None:
    from app.utils.logger import JsonFormatter

    with patch("app.utils.logger.settings") as mock_settings:
        mock_settings.log_level = "DEBUG"
        mock_settings.log_format = "json"

        from app.utils.logger import setup_logging

        setup_logging()

    root = logging.getLogger()
    handler = root.handlers[0]
    assert isinstance(handler.formatter, JsonFormatter)


def test_log_stage_event() -> None:
    from app.utils.logger import log_stage_event

    with patch("app.utils.logger.get_logger") as mock_get:
        mock_logger = logging.getLogger("test")
        mock_logger.info = lambda *a, **kw: None
        mock_get.return_value = mock_logger
        log_stage_event("router", "시작", topic="AI란?")

import logging

from app.utils.logger import get_logger, log_stage_event, setup_logging


def test_get_logger_returns_named_logger() -> None:
    logger = get_logger("test.module")
    assert logger.name == "test.module"
    assert isinstance(logger, logging.Logger)


def test_setup_logging_configures_root() -> None:
    setup_logging()
    root = logging.getLogger()
    assert root.level in (logging.DEBUG, logging.INFO, logging.WARNING)
    assert len(root.handlers) == 1


def test_setup_logging_suppresses_uvicorn_access() -> None:
    setup_logging()
    uvicorn_logger = logging.getLogger("uvicorn.access")
    assert uvicorn_logger.level == logging.WARNING


def test_log_stage_event_basic() -> None:
    setup_logging()
    logger = logging.getLogger("pipeline.stage")
    logger.setLevel(logging.DEBUG)

    with _CaptureLog(logger) as records:
        log_stage_event("router", "시작")

    assert len(records) == 1
    assert "[router]" in records[0].getMessage()
    assert "시작" in records[0].getMessage()


def test_log_stage_event_with_kwargs() -> None:
    setup_logging()
    logger = logging.getLogger("pipeline.stage")
    logger.setLevel(logging.DEBUG)

    with _CaptureLog(logger) as records:
        log_stage_event("researcher", "완료", count=42, source="blog_kr")

    assert len(records) == 1
    msg = records[0].getMessage()
    assert "count=42" in msg
    assert "source=blog_kr" in msg


def test_log_stage_event_no_kwargs() -> None:
    setup_logging()
    logger = logging.getLogger("pipeline.stage")
    logger.setLevel(logging.DEBUG)

    with _CaptureLog(logger) as records:
        log_stage_event("outliner", "시작됨")

    msg = records[0].getMessage()
    assert msg == "[outliner] 시작됨"


class _CaptureLog:
    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        self.records: list[logging.LogRecord] = []
        self._handler: logging.Handler | None = None

    def __enter__(self) -> list[logging.LogRecord]:
        self._handler = _ListHandler(self.records)
        self._logger.addHandler(self._handler)
        return self.records

    def __exit__(self, *args: object) -> None:
        if self._handler:
            self._logger.removeHandler(self._handler)


class _ListHandler(logging.Handler):
    def __init__(self, records: list[logging.LogRecord]) -> None:
        super().__init__()
        self._records = records

    def emit(self, record: logging.LogRecord) -> None:
        self._records.append(record)

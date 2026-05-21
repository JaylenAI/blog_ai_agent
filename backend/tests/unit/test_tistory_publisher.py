from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.publishers.tistory import TISTORY_EDITOR_SELECTORS, TistoryPublisher


def test_publisher_init() -> None:
    pub = TistoryPublisher("https://jaylenhan.tistory.com/")
    assert pub._blog_url == "https://jaylenhan.tistory.com"


def test_publisher_init_strips_trailing_slash() -> None:
    pub = TistoryPublisher("https://example.tistory.com///")
    assert pub._blog_url == "https://example.tistory.com"


def test_selectors_defined() -> None:
    assert "html_tab" in TISTORY_EDITOR_SELECTORS
    assert "content_area" in TISTORY_EDITOR_SELECTORS
    assert "title_input" in TISTORY_EDITOR_SELECTORS
    assert "publish_button" in TISTORY_EDITOR_SELECTORS


@pytest.mark.asyncio
async def test_publish_no_playwright() -> None:
    pub = TistoryPublisher("https://jaylenhan.tistory.com")

    original_import = __import__

    def mock_import(name, *args, **kwargs):
        if "playwright" in name:
            raise ImportError("no playwright")
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        result = await pub.publish("제목", "<p>내용</p>")

    assert result["success"] is False


@pytest.mark.asyncio
async def test_publish_browser_error() -> None:
    pub = TistoryPublisher("https://jaylenhan.tistory.com")

    mock_page = AsyncMock()
    mock_page.goto = AsyncMock(side_effect=Exception("navigation failed"))
    mock_page.url = ""

    mock_context = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)

    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_browser.close = AsyncMock()

    mock_pw = AsyncMock()
    mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_pw)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    mock_playwright_fn = MagicMock(return_value=mock_cm)

    playwright_module = MagicMock()
    playwright_module.async_playwright = mock_playwright_fn

    with patch.dict("sys.modules", {"playwright.async_api": playwright_module}):
        result = await pub.publish("제목", "<p>내용</p>")

    assert result["success"] is False
    assert "navigation failed" in result["error"]


@pytest.mark.asyncio
async def test_publish_success_flow() -> None:
    pub = TistoryPublisher("https://jaylenhan.tistory.com")

    mock_page = AsyncMock()
    mock_page.url = "https://jaylenhan.tistory.com/manage/newpost"
    mock_page.goto = AsyncMock()
    mock_page.screenshot = AsyncMock()
    mock_page.query_selector = AsyncMock(return_value=None)

    mock_context = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)

    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_browser.close = AsyncMock()

    mock_pw = AsyncMock()
    mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_pw)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    mock_playwright_fn = MagicMock(return_value=mock_cm)

    playwright_module = MagicMock()
    playwright_module.async_playwright = mock_playwright_fn

    with patch.dict("sys.modules", {"playwright.async_api": playwright_module}):
        result = await pub.publish("제목", "<p>내용</p>")

    assert result["success"] is True
    assert "screenshot" in result

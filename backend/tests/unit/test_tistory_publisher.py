from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.publishers.tistory import TISTORY_EDITOR_SELECTORS, TistoryPublisher


def test_publisher_init() -> None:
    pub = TistoryPublisher("https://jaylenhan.tistory.com/")
    assert pub._blog_url == "https://jaylenhan.tistory.com"


def test_publisher_init_strips_trailing_slash() -> None:
    pub = TistoryPublisher("https://example.tistory.com///")
    assert pub._blog_url == "https://example.tistory.com"


def test_publisher_platform_name() -> None:
    pub = TistoryPublisher("https://jaylenhan.tistory.com")
    assert pub.platform_name == "tistory"


def test_selectors_defined() -> None:
    assert "html_tab" in TISTORY_EDITOR_SELECTORS
    assert "content_area" in TISTORY_EDITOR_SELECTORS
    assert "title_input" in TISTORY_EDITOR_SELECTORS
    assert "publish_button" in TISTORY_EDITOR_SELECTORS
    for key, val in TISTORY_EDITOR_SELECTORS.items():
        assert isinstance(val, list), f"{key} should be a list of selectors"


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


def _build_playwright_mocks(
    page_url: str = "https://jaylenhan.tistory.com/manage/newpost",
) -> tuple[MagicMock, AsyncMock, AsyncMock]:
    """Playwright browser/context/page mock 생성 헬퍼.
    Returns: (playwright_module, mock_browser, mock_page)
    """
    mock_page = AsyncMock()
    mock_page.url = page_url
    mock_page.goto = AsyncMock()
    mock_page.screenshot = AsyncMock()
    mock_page.query_selector = AsyncMock(return_value=None)
    mock_page.evaluate = AsyncMock()

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

    return playwright_module, mock_browser, mock_page


# ── 로그인 감지 + _wait_for_login ──


@pytest.mark.asyncio
async def test_publish_triggers_login_wait_on_login_url() -> None:
    """page.url에 'login'이 포함되면 _wait_for_login을 호출"""
    pw_module, mock_browser, mock_page = _build_playwright_mocks()
    mock_page.url = "https://accounts.kakao.com/login?continue=..."

    mock_page.wait_for_url = AsyncMock()

    pub = TistoryPublisher("https://jaylenhan.tistory.com")

    with patch.dict("sys.modules", {"playwright.async_api": pw_module}):
        result = await pub.publish("제목", "<p>내용</p>")

    assert result["success"] is True
    mock_page.wait_for_url.assert_awaited_once()


@pytest.mark.asyncio
async def test_publish_triggers_login_wait_on_accounts_url() -> None:
    """page.url에 'accounts'가 포함되면 _wait_for_login을 호출"""
    pw_module, mock_browser, mock_page = _build_playwright_mocks()
    mock_page.url = "https://accounts.kakao.com/weblogin"

    mock_page.wait_for_url = AsyncMock()

    pub = TistoryPublisher("https://jaylenhan.tistory.com")

    with patch.dict("sys.modules", {"playwright.async_api": pw_module}):
        result = await pub.publish("제목", "<p>내용</p>")

    assert result["success"] is True
    mock_page.wait_for_url.assert_awaited_once()


@pytest.mark.asyncio
async def test_wait_for_login_timeout() -> None:
    """wait_for_url이 타임아웃하면 RuntimeError 발생 → publish는 error 반환"""
    pw_module, mock_browser, mock_page = _build_playwright_mocks()
    mock_page.url = "https://accounts.kakao.com/login"

    mock_page.wait_for_url = AsyncMock(
        side_effect=Exception("Timeout 300000ms exceeded")
    )

    pub = TistoryPublisher("https://jaylenhan.tistory.com")

    with patch.dict("sys.modules", {"playwright.async_api": pw_module}):
        result = await pub.publish("제목", "<p>내용</p>")

    assert result["success"] is False
    assert "로그인 타임아웃" in result["error"]


# ── _fill_editor: title 입력 ──


@pytest.mark.asyncio
async def test_fill_editor_fills_title() -> None:
    """title input 요소가 있으면 fill 호출"""
    pw_module, mock_browser, mock_page = _build_playwright_mocks()

    mock_title_el = AsyncMock()

    async def query_selector_side_effect(selector: str):
        if "title" in selector or 'name="title"' in selector:
            return mock_title_el
        return None

    mock_page.query_selector = AsyncMock(side_effect=query_selector_side_effect)

    pub = TistoryPublisher("https://jaylenhan.tistory.com")

    with patch.dict("sys.modules", {"playwright.async_api": pw_module}):
        result = await pub.publish("테스트 제목", "<p>내용</p>")

    assert result["success"] is True
    mock_title_el.fill.assert_awaited_once_with("테스트 제목")


# ── _fill_editor: HTML 탭 클릭 ──


@pytest.mark.asyncio
async def test_fill_editor_clicks_html_tab() -> None:
    """html_tab 버튼이 있으면 click 호출"""
    pw_module, mock_browser, mock_page = _build_playwright_mocks()

    mock_html_btn = AsyncMock()

    async def query_selector_side_effect(selector: str):
        if "html" in selector.lower() or "data-mode" in selector:
            return mock_html_btn
        return None

    mock_page.query_selector = AsyncMock(side_effect=query_selector_side_effect)

    pub = TistoryPublisher("https://jaylenhan.tistory.com")

    with patch.dict("sys.modules", {"playwright.async_api": pw_module}), \
         patch("app.publishers.tistory.asyncio.sleep", new_callable=AsyncMock):
        result = await pub.publish("제목", "<p>내용</p>")

    assert result["success"] is True
    mock_html_btn.click.assert_awaited_once()


# ── _fill_editor: content textarea vs CodeMirror ──


@pytest.mark.asyncio
async def test_fill_editor_textarea_content() -> None:
    """content 영역이 textarea이면 fill() 호출"""
    pw_module, mock_browser, mock_page = _build_playwright_mocks()

    mock_content_el = AsyncMock()
    mock_content_el.evaluate = AsyncMock(return_value="TEXTAREA")

    content_sels = set(TISTORY_EDITOR_SELECTORS["content_area"])

    async def query_selector_side_effect(selector: str):
        if selector in content_sels:
            return mock_content_el
        return None

    mock_page.query_selector = AsyncMock(side_effect=query_selector_side_effect)

    pub = TistoryPublisher("https://jaylenhan.tistory.com")

    with patch.dict("sys.modules", {"playwright.async_api": pw_module}):
        result = await pub.publish("제목", "<p>본문</p>")

    assert result["success"] is True
    mock_content_el.fill.assert_awaited_once_with("<p>본문</p>")


@pytest.mark.asyncio
async def test_fill_editor_codemirror_content() -> None:
    """content 영역이 textarea가 아니면 CodeMirror JS 평가"""
    pw_module, mock_browser, mock_page = _build_playwright_mocks()

    mock_content_el = AsyncMock()
    mock_content_el.evaluate = AsyncMock(return_value="DIV")

    content_sels = set(TISTORY_EDITOR_SELECTORS["content_area"])

    async def query_selector_side_effect(selector: str):
        if selector in content_sels:
            return mock_content_el
        return None

    mock_page.query_selector = AsyncMock(side_effect=query_selector_side_effect)

    pub = TistoryPublisher("https://jaylenhan.tistory.com")

    with patch.dict("sys.modules", {"playwright.async_api": pw_module}):
        result = await pub.publish("제목", "<p>CodeMirror 내용</p>")

    assert result["success"] is True
    mock_page.evaluate.assert_awaited_once()
    call_args = mock_page.evaluate.call_args
    assert "CodeMirror" in call_args[0][0]
    assert call_args[0][1] == {"content": "<p>CodeMirror 내용</p>"}


# ── _fill_editor: category 선택 ──


@pytest.mark.asyncio
async def test_fill_editor_selects_category() -> None:
    """category가 주어지면 option 매칭 후 select_option 호출"""
    pw_module, mock_browser, mock_page = _build_playwright_mocks()

    mock_opt1 = AsyncMock()
    mock_opt1.inner_text = AsyncMock(return_value="일반")
    mock_opt1.get_attribute = AsyncMock(return_value="1")

    mock_opt2 = AsyncMock()
    mock_opt2.inner_text = AsyncMock(return_value="개발/IT")
    mock_opt2.get_attribute = AsyncMock(return_value="2")

    mock_cat_el = AsyncMock()
    mock_cat_el.query_selector_all = AsyncMock(return_value=[mock_opt1, mock_opt2])

    cat_sels = set(TISTORY_EDITOR_SELECTORS["category_select"])

    async def query_selector_side_effect(selector: str):
        if selector in cat_sels:
            return mock_cat_el
        return None

    mock_page.query_selector = AsyncMock(side_effect=query_selector_side_effect)

    pub = TistoryPublisher("https://jaylenhan.tistory.com")

    with patch.dict("sys.modules", {"playwright.async_api": pw_module}):
        result = await pub.publish("제목", "<p>내용</p>", category="개발")

    assert result["success"] is True
    mock_cat_el.select_option.assert_awaited_once_with("2")


@pytest.mark.asyncio
async def test_fill_editor_category_no_match() -> None:
    """매칭되는 option이 없으면 select_option 미호출"""
    pw_module, mock_browser, mock_page = _build_playwright_mocks()

    mock_opt = AsyncMock()
    mock_opt.inner_text = AsyncMock(return_value="일반")
    mock_opt.get_attribute = AsyncMock(return_value="1")

    mock_cat_el = AsyncMock()
    mock_cat_el.query_selector_all = AsyncMock(return_value=[mock_opt])

    cat_sels = set(TISTORY_EDITOR_SELECTORS["category_select"])

    async def query_selector_side_effect(selector: str):
        if selector in cat_sels:
            return mock_cat_el
        return None

    mock_page.query_selector = AsyncMock(side_effect=query_selector_side_effect)

    pub = TistoryPublisher("https://jaylenhan.tistory.com")

    with patch.dict("sys.modules", {"playwright.async_api": pw_module}):
        result = await pub.publish("제목", "<p>내용</p>", category="존재하지않는카테고리")

    assert result["success"] is True
    mock_cat_el.select_option.assert_not_awaited()


@pytest.mark.asyncio
async def test_fill_editor_category_option_no_value() -> None:
    """option의 value가 None이면 select_option 미호출"""
    pw_module, mock_browser, mock_page = _build_playwright_mocks()

    mock_opt = AsyncMock()
    mock_opt.inner_text = AsyncMock(return_value="개발")
    mock_opt.get_attribute = AsyncMock(return_value=None)

    mock_cat_el = AsyncMock()
    mock_cat_el.query_selector_all = AsyncMock(return_value=[mock_opt])

    cat_sels = set(TISTORY_EDITOR_SELECTORS["category_select"])

    async def query_selector_side_effect(selector: str):
        if selector in cat_sels:
            return mock_cat_el
        return None

    mock_page.query_selector = AsyncMock(side_effect=query_selector_side_effect)

    pub = TistoryPublisher("https://jaylenhan.tistory.com")

    with patch.dict("sys.modules", {"playwright.async_api": pw_module}):
        result = await pub.publish("제목", "<p>내용</p>", category="개발")

    assert result["success"] is True
    mock_cat_el.select_option.assert_not_awaited()


# ── _fill_editor: tags 입력 ──


@pytest.mark.asyncio
async def test_fill_editor_fills_tags() -> None:
    """tags가 주어지면 각 태그별 fill + Enter 입력"""
    pw_module, mock_browser, mock_page = _build_playwright_mocks()

    mock_tag_input = AsyncMock()

    async def query_selector_side_effect(selector: str):
        if "tag" in selector.lower():
            return mock_tag_input
        return None

    mock_page.query_selector = AsyncMock(side_effect=query_selector_side_effect)

    pub = TistoryPublisher("https://jaylenhan.tistory.com")

    with patch.dict("sys.modules", {"playwright.async_api": pw_module}), \
         patch("app.publishers.tistory.asyncio.sleep", new_callable=AsyncMock):
        result = await pub.publish("제목", "<p>내용</p>", tags=["AI", "LLM", "Python"])

    assert result["success"] is True
    assert mock_tag_input.fill.await_count == 3
    assert mock_tag_input.press.await_count == 3
    mock_tag_input.press.assert_awaited_with("Enter")


@pytest.mark.asyncio
async def test_fill_editor_tags_max_10() -> None:
    """tags는 최대 10개만 처리"""
    pw_module, mock_browser, mock_page = _build_playwright_mocks()

    mock_tag_input = AsyncMock()

    async def query_selector_side_effect(selector: str):
        if "tag" in selector.lower():
            return mock_tag_input
        return None

    mock_page.query_selector = AsyncMock(side_effect=query_selector_side_effect)

    many_tags = [f"tag{i}" for i in range(15)]

    pub = TistoryPublisher("https://jaylenhan.tistory.com")

    with patch.dict("sys.modules", {"playwright.async_api": pw_module}), \
         patch("app.publishers.tistory.asyncio.sleep", new_callable=AsyncMock):
        result = await pub.publish("제목", "<p>내용</p>", tags=many_tags)

    assert result["success"] is True
    assert mock_tag_input.fill.await_count == 10


@pytest.mark.asyncio
async def test_fill_editor_tags_no_input_element() -> None:
    """tag input 요소가 없으면 에러 없이 넘어감"""
    pw_module, mock_browser, mock_page = _build_playwright_mocks()

    mock_page.query_selector = AsyncMock(return_value=None)

    pub = TistoryPublisher("https://jaylenhan.tistory.com")

    with patch.dict("sys.modules", {"playwright.async_api": pw_module}), \
         patch("app.publishers.tistory.asyncio.sleep", new_callable=AsyncMock):
        result = await pub.publish("제목", "<p>내용</p>", tags=["AI"])

    assert result["success"] is True

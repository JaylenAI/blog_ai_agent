import asyncio
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger(__name__)

TISTORY_EDITOR_SELECTORS = {
    "html_tab": 'button[data-mode="html"], .btn_html, #editor-mode-html',
    "content_area": '#content, .CodeMirror, textarea[name="content"]',
    "title_input": '#title, input[name="title"]',
    "category_select": '#category, select[name="category"]',
    "publish_button": '#publish-layer-btn, .btn_publish, button.btn_save',
}


class TistoryPublisher:
    def __init__(self, blog_url: str) -> None:
        self._blog_url = blog_url.rstrip("/")

    async def publish(
        self,
        title: str,
        html_content: str,
        *,
        category: str = "",
        tags: list[str] | None = None,
        headless: bool = False,
    ) -> dict:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("Playwright가 설치되지 않았습니다")
            return {"success": False, "error": "playwright 미설치"}

        write_url = f"{self._blog_url}/manage/newpost"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                await page.goto(write_url, wait_until="networkidle", timeout=30000)

                if "login" in page.url.lower() or "accounts" in page.url.lower():
                    logger.info("로그인 필요 — 사용자 수동 로그인 대기")
                    await self._wait_for_login(page)

                await self._fill_editor(page, title, html_content, category, tags)

                screenshot_path = Path("/tmp/tistory_preview.png")
                await page.screenshot(path=str(screenshot_path))
                logger.info("미리보기 스크린샷: %s", screenshot_path)

                logger.info("Tistory 에디터 준비 완료 — 수동 발행 필요")
                return {
                    "success": True,
                    "screenshot": str(screenshot_path),
                    "message": "에디터에 내용이 입력되었습니다. 수동으로 발행하세요.",
                }

            except Exception as e:
                logger.error("Tistory 발행 실패: %s", e)
                return {"success": False, "error": str(e)}
            finally:
                await browser.close()

    async def _wait_for_login(self, page) -> None:  # noqa: ANN001
        logger.info("브라우저에서 직접 로그인해주세요 (최대 5분 대기)")
        try:
            await page.wait_for_url(
                f"**{self._blog_url}/manage/**",
                timeout=300000,
            )
            logger.info("로그인 완료 감지")
        except Exception as e:
            raise RuntimeError("로그인 타임아웃 (5분 초과)") from e

    async def _fill_editor(
        self,
        page,  # noqa: ANN001
        title: str,
        html_content: str,
        category: str,
        tags: list[str] | None,
    ) -> None:
        title_sel = TISTORY_EDITOR_SELECTORS["title_input"]
        title_el = await page.query_selector(title_sel)
        if title_el:
            await title_el.fill(title)

        html_tab = TISTORY_EDITOR_SELECTORS["html_tab"]
        html_btn = await page.query_selector(html_tab)
        if html_btn:
            await html_btn.click()
            await asyncio.sleep(1)

        content_sel = TISTORY_EDITOR_SELECTORS["content_area"]
        content_el = await page.query_selector(content_sel)
        if content_el:
            tag_name = await content_el.evaluate("el => el.tagName")
            if tag_name.lower() == "textarea":
                await content_el.fill(html_content)
            else:
                await page.evaluate(
                    """(args) => {
                        const cm = document.querySelector('.CodeMirror');
                        if (cm && cm.CodeMirror) {
                            cm.CodeMirror.setValue(args.content);
                        }
                    }""",
                    {"content": html_content},
                )

        if category:
            cat_sel = TISTORY_EDITOR_SELECTORS["category_select"]
            cat_el = await page.query_selector(cat_sel)
            if cat_el:
                options = await cat_el.query_selector_all("option")
                for opt in options:
                    text = await opt.inner_text()
                    if category.lower() in text.lower():
                        value = await opt.get_attribute("value")
                        if value:
                            await cat_el.select_option(value)
                        break

        if tags:
            for tag in tags[:10]:
                tag_input = await page.query_selector(
                    'input[name="tag"], .tag_input input'
                )
                if tag_input:
                    await tag_input.fill(tag)
                    await tag_input.press("Enter")
                    await asyncio.sleep(0.3)

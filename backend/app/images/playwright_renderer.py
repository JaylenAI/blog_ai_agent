from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger(__name__)

_THUMBNAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  width: 1200px; height: 630px;
  display: flex; align-items: center; justify-content: center;
  font-family: 'Apple SD Gothic Neo', 'Noto Sans CJK KR', sans-serif;
  background: {bg};
  overflow: hidden;
}}
.card {{
  width: 1120px; padding: 60px;
  display: flex; flex-direction: column; justify-content: center; gap: 24px;
}}
.category {{
  font-size: 16px; font-weight: 600; color: {accent};
  text-transform: uppercase; letter-spacing: 1.5px;
}}
.title {{
  font-size: 48px; font-weight: 800; line-height: 1.3;
  color: {title_color};
}}
.subtitle {{
  font-size: 20px; line-height: 1.5; color: {sub_color};
}}
.footer {{
  display: flex; align-items: center; gap: 12px;
  margin-top: auto; font-size: 14px; color: {foot_color};
}}
.dot {{ width: 4px; height: 4px; border-radius: 50%; background: {foot_color}; }}
</style>
</head>
<body>
<div class="card">
  <div class="category">{category}</div>
  <div class="title">{title}</div>
  <div class="subtitle">{subtitle}</div>
  <div class="footer">
    <span>{author}</span>
    <span class="dot"></span>
    <span>{blog_name}</span>
  </div>
</div>
</body>
</html>
"""

_INFOGRAPHIC_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  width: 1200px; height: {height}px;
  font-family: 'Apple SD Gothic Neo', 'Noto Sans CJK KR', sans-serif;
  background: {bg}; padding: 48px;
}}
.info-title {{
  font-size: 28px; font-weight: 700; color: {title_color};
  margin-bottom: 32px; text-align: center;
}}
.info-grid {{
  display: grid; grid-template-columns: repeat({cols}, 1fr);
  gap: 20px;
}}
.info-item {{
  background: {item_bg}; border-radius: 12px; padding: 24px;
  border: 1px solid {border};
}}
.info-item-num {{
  font-size: 32px; font-weight: 800; color: {accent};
  margin-bottom: 8px;
}}
.info-item-title {{
  font-size: 16px; font-weight: 600; color: {title_color};
  margin-bottom: 6px;
}}
.info-item-desc {{
  font-size: 13px; line-height: 1.5; color: {sub_color};
}}
</style>
</head>
<body>
<div class="info-title">{title}</div>
<div class="info-grid">{items_html}</div>
</body>
</html>
"""

_COMPARISON_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  width: 1200px; height: {height}px;
  font-family: 'Apple SD Gothic Neo', 'Noto Sans CJK KR', sans-serif;
  background: {bg}; padding: 48px;
}}
.comp-title {{
  font-size: 28px; font-weight: 700; color: {title_color};
  margin-bottom: 24px; text-align: center;
}}
table {{
  width: 100%; border-collapse: collapse;
  font-size: 14px; color: {title_color};
}}
th {{
  background: {accent}; color: #fff; padding: 14px 16px;
  text-align: left; font-weight: 600; font-size: 15px;
}}
th:first-child {{ border-radius: 8px 0 0 0; }}
th:last-child {{ border-radius: 0 8px 0 0; }}
td {{
  padding: 12px 16px; border-bottom: 1px solid {border};
}}
tr:nth-child(even) td {{ background: {item_bg}; }}
</style>
</head>
<body>
<div class="comp-title">{title}</div>
<table>
<thead><tr>{headers_html}</tr></thead>
<tbody>{rows_html}</tbody>
</table>
</body>
</html>
"""

DARK_THEME = {
    "bg": "#18181A",
    "title_color": "#ECECEA",
    "sub_color": "#C9C9C5",
    "foot_color": "#8A8A85",
    "accent": "#7C8AFF",
    "item_bg": "#1F1F22",
    "border": "#2D2D31",
}

LIGHT_THEME = {
    "bg": "#FFFFFF",
    "title_color": "#1A1A1A",
    "sub_color": "#555555",
    "foot_color": "#999999",
    "accent": "#4F5BD5",
    "item_bg": "#F8F8F8",
    "border": "#E5E5E5",
}


async def _take_screenshot(
    html: str, output_path: Path, width: int = 1200, height: int = 630,
) -> bool:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("playwright 미설치 — HTML→PNG 건너뜀")
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": width, "height": height})
            await page.set_content(html)
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path=str(output_path), type="png")
            await browser.close()

        if output_path.exists() and output_path.stat().st_size > 100:
            logger.info("HTML→PNG 성공: %s", output_path.name)
            return True

        logger.warning("스크린샷 파일 검증 실패: %s", output_path.name)
        return False

    except Exception as e:
        logger.error("Playwright 스크린샷 실패: %s", e)
        return False


async def render_thumbnail(
    output_path: Path,
    *,
    title: str,
    category: str = "Tech Blog",
    subtitle: str = "",
    author: str = "Jaylen H.",
    blog_name: str = "AI의 정석",
    theme: str = "dark",
) -> bool:
    colors = DARK_THEME if theme == "dark" else LIGHT_THEME
    html = _THUMBNAIL_TEMPLATE.format(
        title=_escape(title),
        category=_escape(category),
        subtitle=_escape(subtitle),
        author=_escape(author),
        blog_name=_escape(blog_name),
        **colors,
    )
    return await _take_screenshot(html, output_path)


async def render_infographic(
    output_path: Path,
    *,
    title: str,
    items: list[dict],
    cols: int = 2,
    theme: str = "dark",
) -> bool:
    colors = DARK_THEME if theme == "dark" else LIGHT_THEME
    items_html = ""
    for i, item in enumerate(items):
        items_html += (
            f'<div class="info-item">'
            f'<div class="info-item-num">{i + 1:02d}</div>'
            f'<div class="info-item-title">{_escape(item.get("title", ""))}</div>'
            f'<div class="info-item-desc">{_escape(item.get("desc", ""))}</div>'
            f'</div>'
        )

    rows = (len(items) + cols - 1) // cols
    height = 48 + 32 + 40 + rows * 140 + 48

    html = _INFOGRAPHIC_TEMPLATE.format(
        title=_escape(title),
        items_html=items_html,
        cols=cols,
        height=height,
        **colors,
    )
    return await _take_screenshot(html, output_path, height=height)


async def render_comparison(
    output_path: Path,
    *,
    title: str,
    headers: list[str],
    rows: list[list[str]],
    theme: str = "dark",
) -> bool:
    colors = DARK_THEME if theme == "dark" else LIGHT_THEME
    headers_html = "".join(f"<th>{_escape(h)}</th>" for h in headers)
    rows_html = ""
    for row in rows:
        cells = "".join(f"<td>{_escape(c)}</td>" for c in row)
        rows_html += f"<tr>{cells}</tr>"

    height = 48 + 28 + 24 + 48 + len(rows) * 48 + 48

    html = _COMPARISON_TEMPLATE.format(
        title=_escape(title),
        headers_html=headers_html,
        rows_html=rows_html,
        height=height,
        **colors,
    )
    return await _take_screenshot(html, output_path, height=height)


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

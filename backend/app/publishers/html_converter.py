import re

from app.utils.logger import get_logger

logger = get_logger(__name__)


def markdown_to_html(content: str, *, image_base_url: str = "") -> str:
    lines = content.split("\n")
    html_parts: list[str] = []
    in_code_block = False
    code_lang = ""
    code_lines: list[str] = []
    in_list = False
    list_items: list[str] = []

    for line in lines:
        if line.strip().startswith("```"):
            if in_code_block:
                code = "\n".join(code_lines)
                lang_attr = f' class="language-{code_lang}"' if code_lang else ""
                html_parts.append(
                    f"<pre><code{lang_attr}>{_escape_html(code)}</code></pre>"
                )
                code_lines = []
                code_lang = ""
                in_code_block = False
            else:
                if in_list:
                    html_parts.append(_flush_list(list_items))
                    in_list = False
                in_code_block = True
                code_lang = line.strip().removeprefix("```").strip()
                if code_lang == "mermaid":
                    code_lang = ""
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        stripped = line.strip()

        if not stripped:
            if in_list:
                html_parts.append(_flush_list(list_items))
                in_list = False
            continue

        if stripped.startswith("# "):
            if in_list:
                html_parts.append(_flush_list(list_items))
                in_list = False
            text = _inline_format(stripped[2:])
            html_parts.append(f"<h1>{text}</h1>")
        elif stripped.startswith("## "):
            if in_list:
                html_parts.append(_flush_list(list_items))
                in_list = False
            text = _inline_format(stripped[3:])
            html_parts.append(f"<h2>{text}</h2>")
        elif stripped.startswith("### "):
            if in_list:
                html_parts.append(_flush_list(list_items))
                in_list = False
            text = _inline_format(stripped[4:])
            html_parts.append(f"<h3>{text}</h3>")
        elif stripped.startswith("- ") or stripped.startswith("* "):
            in_list = True
            list_items.append(_inline_format(stripped[2:]))
        elif re.match(r"^\d+\.\s", stripped):
            in_list = True
            text = re.sub(r"^\d+\.\s", "", stripped)
            list_items.append(_inline_format(text))
        elif stripped.startswith("!["):
            if in_list:
                html_parts.append(_flush_list(list_items))
                in_list = False
            html_parts.append(_convert_image(stripped, image_base_url))
        elif stripped.startswith("*") and stripped.endswith("*") and stripped.startswith("*그림"):
            html_parts.append(f'<p class="image-caption"><em>{stripped.strip("*")}</em></p>')
        elif stripped.startswith(">"):
            if in_list:
                html_parts.append(_flush_list(list_items))
                in_list = False
            quote_text = _inline_format(stripped.lstrip("> "))
            html_parts.append(f"<blockquote><p>{quote_text}</p></blockquote>")
        elif stripped.startswith("---"):
            if in_list:
                html_parts.append(_flush_list(list_items))
                in_list = False
            html_parts.append("<hr>")
        else:
            if in_list:
                html_parts.append(_flush_list(list_items))
                in_list = False
            text = _inline_format(stripped)
            html_parts.append(f"<p>{text}</p>")

    if in_list:
        html_parts.append(_flush_list(list_items))

    return "\n".join(html_parts)


def _flush_list(items: list[str]) -> str:
    html = "<ul>\n"
    for item in items:
        html += f"  <li>{item}</li>\n"
    html += "</ul>"
    items.clear()
    return html


def _inline_format(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    return text


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _convert_image(line: str, base_url: str) -> str:
    match = re.match(r"!\[(.*)?\]\((.+?)\)", line)
    if not match:
        return f"<p>{_escape_html(line)}</p>"

    alt = match.group(1) or ""
    src = match.group(2)

    if base_url and not src.startswith(("http://", "https://")):
        src = f"{base_url.rstrip('/')}/{src.lstrip('/')}"

    return f'<figure><img src="{src}" alt="{_escape_html(alt)}" loading="lazy"></figure>'


def convert_for_tistory(
    content: str,
    meta: dict,
    *,
    image_base_url: str = "",
) -> str:
    html_body = markdown_to_html(content, image_base_url=image_base_url)

    title = meta.get("title", "")
    keywords = meta.get("seo_keywords", [])

    json_ld = _build_json_ld(title, meta)
    meta_tags = _build_meta_tags(title, keywords, meta)

    return f"{meta_tags}\n{json_ld}\n{html_body}"


def _build_meta_tags(title: str, keywords: list[str], meta: dict) -> str:
    description = meta.get("description", title)
    kw_str = ", ".join(keywords[:10])
    blog_url = meta.get("blog_url", "")
    og_image = meta.get("og_image", "")
    parts = [
        f'<meta name="description" content="{_escape_html(description)}">',
        f'<meta name="keywords" content="{_escape_html(kw_str)}">',
        f'<meta property="og:type" content="article">',
        f'<meta property="og:title" content="{_escape_html(title)}">',
        f'<meta property="og:description" content="{_escape_html(description)}">',
    ]
    if blog_url:
        parts.append(f'<meta property="og:url" content="{_escape_html(blog_url)}">')
    if og_image:
        parts.append(f'<meta property="og:image" content="{_escape_html(og_image)}">')
    parts.extend([
        f'<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{_escape_html(title)}">',
        f'<meta name="twitter:description" content="{_escape_html(description)}">',
    ])
    if og_image:
        parts.append(f'<meta name="twitter:image" content="{_escape_html(og_image)}">')
    return "\n".join(parts)


def _build_json_ld(title: str, meta: dict) -> str:
    import json
    from datetime import datetime, timezone

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+09:00")
    description = meta.get("description", title)

    ld: dict = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title,
        "description": description,
        "author": {
            "@type": "Person",
            "name": meta.get("author", "Jaylen H"),
        },
        "publisher": {
            "@type": "Organization",
            "name": meta.get("publisher_name", "AI의 정석"),
        },
        "datePublished": meta.get("date_published", now_iso),
        "dateModified": meta.get("date_modified", now_iso),
        "keywords": meta.get("seo_keywords", []),
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": meta.get("blog_url", ""),
        },
    }
    if meta.get("og_image"):
        ld["image"] = meta["og_image"]
    if meta.get("author_url"):
        ld["author"]["url"] = meta["author_url"]

    body = json.dumps(ld, ensure_ascii=False, indent=2)
    return f'<script type="application/ld+json">\n{body}\n</script>'

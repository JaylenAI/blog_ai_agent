from app.publishers.html_converter import (
    convert_for_tistory,
    markdown_to_html,
)


def test_heading_conversion() -> None:
    md = "# 제목\n\n## 부제목\n\n### 소제목"
    html = markdown_to_html(md)
    assert "<h1>제목</h1>" in html
    assert "<h2>부제목</h2>" in html
    assert "<h3>소제목</h3>" in html


def test_paragraph_conversion() -> None:
    md = "일반 텍스트입니다."
    html = markdown_to_html(md)
    assert "<p>일반 텍스트입니다.</p>" in html


def test_bold_and_italic() -> None:
    md = "**굵은** 텍스트와 *기울임* 텍스트"
    html = markdown_to_html(md)
    assert "<strong>굵은</strong>" in html
    assert "<em>기울임</em>" in html


def test_inline_code() -> None:
    md = "`코드` 인라인"
    html = markdown_to_html(md)
    assert "<code>코드</code>" in html


def test_link_conversion() -> None:
    md = "[링크](https://example.com)"
    html = markdown_to_html(md)
    assert '<a href="https://example.com">링크</a>' in html


def test_code_block() -> None:
    md = "```python\nprint('hello')\n```"
    html = markdown_to_html(md)
    assert '<pre><code class="language-python">' in html
    assert "print(&#x27;hello&#x27;)" in html or "print(" in html


def test_unordered_list() -> None:
    md = "- 항목 1\n- 항목 2\n- 항목 3"
    html = markdown_to_html(md)
    assert "<ul>" in html
    assert "<li>항목 1</li>" in html
    assert "<li>항목 3</li>" in html


def test_image_conversion() -> None:
    md = "![설명](image.png)"
    html = markdown_to_html(md)
    assert '<img src="image.png"' in html
    assert 'alt="설명"' in html
    assert "loading=\"lazy\"" in html


def test_image_with_base_url() -> None:
    md = "![다이어그램](images/diag.png)"
    html = markdown_to_html(md, image_base_url="https://cdn.example.com")
    assert 'src="https://cdn.example.com/images/diag.png"' in html


def test_blockquote() -> None:
    md = "> 인용문입니다"
    html = markdown_to_html(md)
    assert "<blockquote>" in html
    assert "인용문입니다" in html


def test_horizontal_rule() -> None:
    md = "---"
    html = markdown_to_html(md)
    assert "<hr>" in html


def test_mermaid_code_block_treated_as_code() -> None:
    md = "```mermaid\ngraph TD\n  A-->B\n```"
    html = markdown_to_html(md)
    assert "<pre><code>" in html


def test_convert_for_tistory_includes_meta() -> None:
    content = "## 테스트\n\n본문입니다."
    meta = {
        "title": "테스트 제목",
        "seo_keywords": ["키워드1", "키워드2"],
        "description": "테스트 설명",
    }
    html = convert_for_tistory(content, meta)

    assert 'meta name="description"' in html
    assert 'meta name="keywords"' in html
    assert "application/ld+json" in html
    assert "BlogPosting" in html
    assert "<h2>테스트</h2>" in html


def test_convert_for_tistory_json_ld() -> None:
    content = "# 제목"
    meta = {"title": "JSON-LD 테스트", "author": "TestUser"}
    html = convert_for_tistory(content, meta)

    assert '"@type": "BlogPosting"' in html
    assert '"headline": "JSON-LD 테스트"' in html
    assert "TestUser" in html


def test_escape_html_in_code() -> None:
    md = "```\n<div>test</div>\n```"
    html = markdown_to_html(md)
    assert "&lt;div&gt;" in html
    assert "&lt;/div&gt;" in html


def test_image_caption() -> None:
    md = "*그림 1. 아키텍처 다이어그램.*"
    html = markdown_to_html(md)
    assert "image-caption" in html
    assert "아키텍처 다이어그램" in html


def test_list_interrupted_by_heading() -> None:
    md = "- 항목1\n- 항목2\n## 제목"
    html = markdown_to_html(md)
    assert "<ul>" in html
    assert "<h2>제목</h2>" in html
    assert html.index("</ul>") < html.index("<h2>")


def test_list_interrupted_by_image() -> None:
    md = "- 항목1\n![alt](img.png)"
    html = markdown_to_html(md)
    assert "<ul>" in html
    assert '<img src="img.png"' in html


def test_list_interrupted_by_blockquote() -> None:
    md = "- 항목1\n> 인용문"
    html = markdown_to_html(md)
    assert "<ul>" in html
    assert "<blockquote>" in html


def test_list_interrupted_by_hr() -> None:
    md = "- 항목1\n---"
    html = markdown_to_html(md)
    assert "<ul>" in html
    assert "<hr>" in html


def test_list_interrupted_by_paragraph() -> None:
    md = "- 항목1\n\n일반 문단"
    html = markdown_to_html(md)
    assert "<ul>" in html
    assert "<p>일반 문단</p>" in html


def test_list_interrupted_by_code_block() -> None:
    md = "- 항목1\n```python\ncode\n```"
    html = markdown_to_html(md)
    assert "<ul>" in html
    assert "<pre><code" in html


def test_ordered_list() -> None:
    md = "1. 첫째\n2. 둘째"
    html = markdown_to_html(md)
    assert "<li>첫째</li>" in html
    assert "<li>둘째</li>" in html


def test_asterisk_list() -> None:
    md = "* 별표 항목"
    html = markdown_to_html(md)
    assert "<li>별표 항목</li>" in html


def test_h1_interrupts_list() -> None:
    md = "- 항목\n# 큰 제목"
    html = markdown_to_html(md)
    assert "<h1>큰 제목</h1>" in html


def test_h3_interrupts_list() -> None:
    md = "- 항목\n### 작은 제목"
    html = markdown_to_html(md)
    assert "<h3>작은 제목</h3>" in html


def test_invalid_image_syntax() -> None:
    from app.publishers.html_converter import _convert_image
    result = _convert_image("not an image", "")
    assert "<p>" in result

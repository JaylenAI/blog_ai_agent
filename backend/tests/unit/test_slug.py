from app.utils.slug import generate_slug


def test_basic_slug() -> None:
    assert generate_slug("Hello World") == "hello-world"


def test_korean_slug() -> None:
    slug = generate_slug("AI란 무엇인가?")
    assert "ai란" in slug
    assert "무엇인가" in slug
    assert "?" not in slug


def test_special_characters_removed() -> None:
    slug = generate_slug("Hello! @World# $Test%")
    assert slug == "hello-world-test"


def test_multiple_spaces() -> None:
    slug = generate_slug("hello    world")
    assert slug == "hello-world"


def test_leading_trailing_hyphens() -> None:
    slug = generate_slug("  -hello world-  ")
    assert slug == "hello-world"


def test_empty_string() -> None:
    assert generate_slug("") == "untitled"


def test_max_length() -> None:
    long_text = "a" * 300
    slug = generate_slug(long_text)
    assert len(slug) <= 200

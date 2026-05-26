from __future__ import annotations

import pytest

from app.publishers import PUBLISHER_REGISTRY, get_publisher
from app.publishers.base import PublisherAdapter
from app.publishers.tistory import TistoryPublisher
from app.publishers.wordpress import WordPressPublisher


def test_registry_has_tistory() -> None:
    assert "tistory" in PUBLISHER_REGISTRY
    assert PUBLISHER_REGISTRY["tistory"] is TistoryPublisher


def test_registry_has_wordpress() -> None:
    assert "wordpress" in PUBLISHER_REGISTRY
    assert PUBLISHER_REGISTRY["wordpress"] is WordPressPublisher


def test_get_publisher_tistory() -> None:
    pub = get_publisher("tistory", blog_url="https://test.tistory.com")
    assert isinstance(pub, TistoryPublisher)
    assert isinstance(pub, PublisherAdapter)


def test_get_publisher_wordpress() -> None:
    pub = get_publisher("wordpress", site_url="https://example.com", username="u", app_password="p")
    assert isinstance(pub, WordPressPublisher)
    assert isinstance(pub, PublisherAdapter)


def test_get_publisher_unknown() -> None:
    with pytest.raises(ValueError, match="지원하지 않는 플랫폼"):
        get_publisher("medium")

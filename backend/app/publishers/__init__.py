from app.publishers.base import PublisherAdapter
from app.publishers.tistory import TistoryPublisher
from app.publishers.wordpress import WordPressPublisher

PUBLISHER_REGISTRY: dict[str, type[PublisherAdapter]] = {
    "tistory": TistoryPublisher,
    "wordpress": WordPressPublisher,
}


def get_publisher(platform: str, **kwargs: object) -> PublisherAdapter:
    cls = PUBLISHER_REGISTRY.get(platform)
    if not cls:
        raise ValueError(f"지원하지 않는 플랫폼: {platform} (가능: {list(PUBLISHER_REGISTRY)})")
    return cls(**kwargs)

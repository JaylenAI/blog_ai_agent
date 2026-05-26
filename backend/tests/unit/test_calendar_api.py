from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from httpx import AsyncClient

from app.dependencies import get_article_service


def _make_article(
    article_id: int = 1,
    title: str = "테스트",
    topic: str = "테스트 주제",
    status: str = "draft",
    scheduled_at: datetime | None = None,
    published_at: datetime | None = None,
) -> MagicMock:
    a = MagicMock()
    a.id = article_id
    a.title = title
    a.topic = topic
    a.status = MagicMock(value=status)
    a.scheduled_at = scheduled_at
    a.published_at = published_at
    return a


async def test_get_calendar_empty(client: AsyncClient) -> None:
    mock_service = AsyncMock()
    mock_service.list_all = AsyncMock(return_value=([], 0))

    app = client._transport.app
    app.dependency_overrides[get_article_service] = lambda: mock_service

    response = await client.get("/api/v1/calendar")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] == []

    app.dependency_overrides.pop(get_article_service, None)


async def test_get_calendar_with_articles(client: AsyncClient) -> None:
    articles = [
        _make_article(1, "글1", "주제1"),
        _make_article(2, "글2", "주제2", scheduled_at=datetime(2026, 6, 1, 10, 0)),
    ]
    mock_service = AsyncMock()
    mock_service.list_all = AsyncMock(return_value=(articles, 2))

    app = client._transport.app
    app.dependency_overrides[get_article_service] = lambda: mock_service

    response = await client.get("/api/v1/calendar")
    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) == 2
    assert body["data"][0]["article_id"] == 1
    assert body["data"][1]["scheduled_at"] is not None

    app.dependency_overrides.pop(get_article_service, None)


async def test_schedule_article_success(client: AsyncClient) -> None:
    article = _make_article(1, "글1", "주제1")
    mock_session = AsyncMock()
    mock_service = AsyncMock()
    mock_service.get_by_id = AsyncMock(return_value=article)
    mock_service._repo = MagicMock()
    mock_service._repo._session = mock_session

    app = client._transport.app
    app.dependency_overrides[get_article_service] = lambda: mock_service

    response = await client.put(
        "/api/v1/calendar/1/schedule",
        json={"scheduled_at": "2026-06-01T10:00:00"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["article_id"] == 1

    app.dependency_overrides.pop(get_article_service, None)


async def test_schedule_article_not_found(client: AsyncClient) -> None:
    mock_service = AsyncMock()
    mock_service.get_by_id = AsyncMock(return_value=None)

    app = client._transport.app
    app.dependency_overrides[get_article_service] = lambda: mock_service

    response = await client.put(
        "/api/v1/calendar/9999/schedule",
        json={"scheduled_at": "2026-06-01T10:00:00"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False

    app.dependency_overrides.pop(get_article_service, None)


async def test_unschedule_article_success(client: AsyncClient) -> None:
    article = _make_article(1, "글1", "주제1", scheduled_at=datetime(2026, 6, 1))
    mock_session = AsyncMock()
    mock_service = AsyncMock()
    mock_service.get_by_id = AsyncMock(return_value=article)
    mock_service._repo = MagicMock()
    mock_service._repo._session = mock_session

    app = client._transport.app
    app.dependency_overrides[get_article_service] = lambda: mock_service

    response = await client.delete("/api/v1/calendar/1/schedule")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["scheduled_at"] is None

    app.dependency_overrides.pop(get_article_service, None)


async def test_unschedule_article_not_found(client: AsyncClient) -> None:
    mock_service = AsyncMock()
    mock_service.get_by_id = AsyncMock(return_value=None)

    app = client._transport.app
    app.dependency_overrides[get_article_service] = lambda: mock_service

    response = await client.delete("/api/v1/calendar/9999/schedule")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False

    app.dependency_overrides.pop(get_article_service, None)

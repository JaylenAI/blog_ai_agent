import json
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient

from app.dependencies import get_article_service, get_file_manager

# --- _load_user_settings / _save_user_settings (unit) ---


def test_load_user_settings_file_exists() -> None:
    from app.api.v1.settings import _load_user_settings

    data = {"obsidian": {"vault_path": "/test"}}
    with patch("app.api.v1.settings.SETTINGS_FILE") as mock_file:
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = json.dumps(data)
        result = _load_user_settings()

    assert result == data


def test_load_user_settings_no_file() -> None:
    from app.api.v1.settings import _load_user_settings

    with patch("app.api.v1.settings.SETTINGS_FILE") as mock_file:
        mock_file.exists.return_value = False
        result = _load_user_settings()

    assert result == {}


def test_save_user_settings() -> None:
    from app.api.v1.settings import _save_user_settings

    data = {"general": {"log_level": "DEBUG"}}
    with patch("app.api.v1.settings.SETTINGS_FILE") as mock_file:
        mock_parent = MagicMock()
        mock_file.parent = mock_parent
        _save_user_settings(data)

    mock_parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_file.write_text.assert_called_once()
    written = mock_file.write_text.call_args[0][0]
    assert json.loads(written) == data


# --- style-guide ---


async def test_get_style_guide_exists(client: AsyncClient) -> None:
    fake_content = "# Blog Style Guide\n\nrules here"
    with patch("app.api.v1.settings.STYLE_GUIDE_PATH") as mock_path:
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = fake_content
        response = await client.get("/api/v1/settings/style-guide")

    assert response.status_code == 200
    assert response.text == fake_content


async def test_get_style_guide_not_found(client: AsyncClient) -> None:
    with patch("app.api.v1.settings.STYLE_GUIDE_PATH") as mock_path:
        mock_path.exists.return_value = False
        response = await client.get("/api/v1/settings/style-guide")

    assert response.status_code == 200
    assert "찾을 수 없습니다" in response.text


# --- obsidian ---


async def test_get_obsidian_settings_default(client: AsyncClient) -> None:
    with patch("app.api.v1.settings._load_user_settings", return_value={}):
        response = await client.get("/api/v1/settings/obsidian")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert "vault_path" in data
    assert data["frontmatter_tags"] == ["blog/published"]
    assert data["auto_save"] is False


async def test_get_obsidian_settings_with_saved(client: AsyncClient) -> None:
    saved = {
        "obsidian": {
            "vault_path": "/my/vault",
            "frontmatter_tags": ["custom/tag"],
            "auto_save": True,
        }
    }
    with patch("app.api.v1.settings._load_user_settings", return_value=saved):
        response = await client.get("/api/v1/settings/obsidian")

    body = response.json()
    assert body["data"]["vault_path"] == "/my/vault"
    assert body["data"]["frontmatter_tags"] == ["custom/tag"]
    assert body["data"]["auto_save"] is True


async def test_update_obsidian_settings(client: AsyncClient) -> None:
    with (
        patch("app.api.v1.settings._load_user_settings", return_value={}),
        patch("app.api.v1.settings._save_user_settings") as mock_save,
    ):
        response = await client.put(
            "/api/v1/settings/obsidian",
            json={
                "vault_path": "/new/vault",
                "frontmatter_tags": ["blog/draft"],
                "auto_save": True,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["vault_path"] == "/new/vault"
    mock_save.assert_called_once()
    saved_data = mock_save.call_args[0][0]
    assert saved_data["obsidian"]["vault_path"] == "/new/vault"


# --- general ---


async def test_get_general_settings_default(client: AsyncClient) -> None:
    with patch("app.api.v1.settings._load_user_settings", return_value={}):
        response = await client.get("/api/v1/settings/general")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert "tistory_blog_url" in data
    assert "stage_timeout" in data
    assert "image_generation_enabled" in data
    assert "max_images_per_article" in data
    assert "log_level" in data


async def test_get_general_settings_with_saved(client: AsyncClient) -> None:
    saved = {
        "general": {
            "tistory_blog_url": "https://myblog.tistory.com",
            "stage_timeout": 300,
            "image_generation_enabled": False,
            "max_images_per_article": 2,
            "log_level": "DEBUG",
        }
    }
    with patch("app.api.v1.settings._load_user_settings", return_value=saved):
        response = await client.get("/api/v1/settings/general")

    body = response.json()
    assert body["data"]["tistory_blog_url"] == "https://myblog.tistory.com"
    assert body["data"]["stage_timeout"] == 300
    assert body["data"]["image_generation_enabled"] is False
    assert body["data"]["max_images_per_article"] == 2
    assert body["data"]["log_level"] == "DEBUG"


async def test_update_general_settings(client: AsyncClient) -> None:
    with (
        patch("app.api.v1.settings._load_user_settings", return_value={}),
        patch("app.api.v1.settings._save_user_settings") as mock_save,
    ):
        response = await client.put(
            "/api/v1/settings/general",
            json={
                "tistory_blog_url": "https://updated.tistory.com",
                "stage_timeout": 900,
                "image_generation_enabled": True,
                "max_images_per_article": 6,
                "log_level": "WARNING",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["tistory_blog_url"] == "https://updated.tistory.com"
    mock_save.assert_called_once()
    saved_data = mock_save.call_args[0][0]
    assert saved_data["general"]["log_level"] == "WARNING"


# --- batch-update ---


async def test_batch_update_all_fields(client: AsyncClient) -> None:
    """category + status + tags 모두 업데이트"""
    mock_article = MagicMock()
    mock_article.slug = "test-slug"

    mock_service = AsyncMock()
    mock_service.get_by_id = AsyncMock(return_value=mock_article)
    mock_service.update = AsyncMock(return_value=mock_article)

    mock_fm = MagicMock()
    mock_fm.read_json.return_value = {"seo_keywords": []}
    mock_fm.write_json = MagicMock()

    app = client._transport.app
    app.dependency_overrides[get_article_service] = lambda: mock_service
    app.dependency_overrides[get_file_manager] = lambda: mock_fm

    response = await client.post(
        "/api/v1/settings/batch-update",
        json={
            "article_ids": [1],
            "category": "AI/ML",
            "tags": ["python", "ai"],
            "status": "review",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["updated"] == 1
    mock_service.update.assert_awaited_once()
    mock_fm.write_json.assert_called_once()

    app.dependency_overrides.pop(get_article_service, None)
    app.dependency_overrides.pop(get_file_manager, None)


async def test_batch_update_skips_missing_articles(client: AsyncClient) -> None:
    mock_service = AsyncMock()
    mock_service.get_by_id = AsyncMock(return_value=None)

    app = client._transport.app
    app.dependency_overrides[get_article_service] = lambda: mock_service

    response = await client.post(
        "/api/v1/settings/batch-update",
        json={
            "article_ids": [9999],
            "category": "Unknown",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["updated"] == 0

    app.dependency_overrides.pop(get_article_service, None)


async def test_batch_update_with_tags_only(client: AsyncClient) -> None:
    mock_article = MagicMock()
    mock_article.slug = "tags-slug"

    mock_service = AsyncMock()
    mock_service.get_by_id = AsyncMock(return_value=mock_article)

    mock_fm = MagicMock()
    mock_fm.read_json.return_value = {"seo_keywords": ["old"]}
    mock_fm.write_json = MagicMock()

    app = client._transport.app
    app.dependency_overrides[get_article_service] = lambda: mock_service
    app.dependency_overrides[get_file_manager] = lambda: mock_fm

    response = await client.post(
        "/api/v1/settings/batch-update",
        json={
            "article_ids": [1],
            "tags": ["new-tag"],
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["updated"] == 1
    mock_service.update.assert_not_awaited()
    mock_fm.write_json.assert_called_once()

    app.dependency_overrides.pop(get_article_service, None)
    app.dependency_overrides.pop(get_file_manager, None)


async def test_batch_update_tags_skips_non_dict_meta(client: AsyncClient) -> None:
    mock_article = MagicMock()
    mock_article.slug = "non-dict"

    mock_service = AsyncMock()
    mock_service.get_by_id = AsyncMock(return_value=mock_article)

    mock_fm = MagicMock()
    mock_fm.read_json.return_value = None
    mock_fm.write_json = MagicMock()

    app = client._transport.app
    app.dependency_overrides[get_article_service] = lambda: mock_service
    app.dependency_overrides[get_file_manager] = lambda: mock_fm

    response = await client.post(
        "/api/v1/settings/batch-update",
        json={
            "article_ids": [1],
            "tags": ["some-tag"],
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["updated"] == 1
    mock_fm.write_json.assert_not_called()

    app.dependency_overrides.pop(get_article_service, None)
    app.dependency_overrides.pop(get_file_manager, None)


async def test_batch_update_category_only(client: AsyncClient) -> None:
    mock_article = MagicMock()
    mock_article.slug = "cat-only"

    mock_service = AsyncMock()
    mock_service.get_by_id = AsyncMock(return_value=mock_article)
    mock_service.update = AsyncMock(return_value=mock_article)

    app = client._transport.app
    app.dependency_overrides[get_article_service] = lambda: mock_service

    response = await client.post(
        "/api/v1/settings/batch-update",
        json={
            "article_ids": [1],
            "category": "DevOps",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["updated"] == 1
    mock_service.update.assert_awaited_once()

    app.dependency_overrides.pop(get_article_service, None)


async def test_batch_update_status_only(client: AsyncClient) -> None:
    mock_article = MagicMock()
    mock_article.slug = "status-only"

    mock_service = AsyncMock()
    mock_service.get_by_id = AsyncMock(return_value=mock_article)
    mock_service.update = AsyncMock(return_value=mock_article)

    app = client._transport.app
    app.dependency_overrides[get_article_service] = lambda: mock_service

    response = await client.post(
        "/api/v1/settings/batch-update",
        json={
            "article_ids": [1],
            "status": "review",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["updated"] == 1
    mock_service.update.assert_awaited_once()

    app.dependency_overrides.pop(get_article_service, None)


async def test_batch_update_multiple_articles(client: AsyncClient) -> None:
    mock_article = MagicMock()
    mock_article.slug = "multi"

    mock_service = AsyncMock()
    mock_service.get_by_id = AsyncMock(return_value=mock_article)
    mock_service.update = AsyncMock(return_value=mock_article)

    app = client._transport.app
    app.dependency_overrides[get_article_service] = lambda: mock_service

    response = await client.post(
        "/api/v1/settings/batch-update",
        json={
            "article_ids": [1, 2, 3],
            "status": "review",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["updated"] == 3
    assert mock_service.get_by_id.await_count == 3

    app.dependency_overrides.pop(get_article_service, None)


async def test_batch_update_no_update_data(client: AsyncClient) -> None:
    """category, status, tags 모두 None인 경우"""
    mock_article = MagicMock()
    mock_article.slug = "no-update"

    mock_service = AsyncMock()
    mock_service.get_by_id = AsyncMock(return_value=mock_article)
    mock_service.update = AsyncMock()

    app = client._transport.app
    app.dependency_overrides[get_article_service] = lambda: mock_service

    response = await client.post(
        "/api/v1/settings/batch-update",
        json={"article_ids": [1]},
    )

    assert response.status_code == 200
    assert response.json()["data"]["updated"] == 1
    mock_service.update.assert_not_awaited()

    app.dependency_overrides.pop(get_article_service, None)


async def test_batch_update_empty_ids(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/settings/batch-update",
        json={"article_ids": [], "category": "Test"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["updated"] == 0

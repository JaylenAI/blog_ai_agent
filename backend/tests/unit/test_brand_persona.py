from __future__ import annotations

from unittest.mock import patch

from httpx import AsyncClient


async def test_get_brand_persona_default(client: AsyncClient) -> None:
    with patch("app.api.v1.settings._load_user_settings", return_value={}):
        response = await client.get("/api/v1/settings/brand-persona")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["name"] == "기본"
    assert data["tone"] == "격식체"
    assert data["emoji_usage"] is False
    assert data["first_person"] == "필자"


async def test_get_brand_persona_with_saved(client: AsyncClient) -> None:
    saved = {
        "brand_persona": {
            "name": "테크 전문가",
            "tone": "반말체",
            "writing_style": "캐주얼 블로거",
            "target_audience": "초보 개발자",
            "vocabulary_level": "초급",
            "emoji_usage": True,
            "first_person": "나",
        }
    }
    with patch("app.api.v1.settings._load_user_settings", return_value=saved):
        response = await client.get("/api/v1/settings/brand-persona")

    body = response.json()
    assert body["data"]["name"] == "테크 전문가"
    assert body["data"]["tone"] == "반말체"
    assert body["data"]["emoji_usage"] is True
    assert body["data"]["first_person"] == "나"


async def test_update_brand_persona(client: AsyncClient) -> None:
    with (
        patch("app.api.v1.settings._load_user_settings", return_value={}),
        patch("app.api.v1.settings._save_user_settings") as mock_save,
    ):
        response = await client.put(
            "/api/v1/settings/brand-persona",
            json={
                "name": "커스텀",
                "tone": "반말체",
                "writing_style": "교육자",
                "target_audience": "학생",
                "vocabulary_level": "중급",
                "emoji_usage": True,
                "first_person": "저",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["name"] == "커스텀"
    assert body["data"]["emoji_usage"] is True
    mock_save.assert_called_once()
    saved_data = mock_save.call_args[0][0]
    assert saved_data["brand_persona"]["name"] == "커스텀"

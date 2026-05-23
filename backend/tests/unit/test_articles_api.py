from pathlib import Path
from unittest.mock import MagicMock, patch

from httpx import AsyncClient

from app.dependencies import get_file_manager


def _override_fm(client: AsyncClient, mock_fm: MagicMock) -> None:
    """FileManager 의존성을 mock으로 교체"""
    client._transport.app.dependency_overrides[get_file_manager] = lambda: mock_fm


async def _create_article(client: AsyncClient, topic: str = "테스트 주제") -> int:
    """테스트용 아티클 생성 후 ID 반환"""
    resp = await client.post("/api/v1/articles", json={"topic": topic})
    return resp.json()["data"]["id"]


async def test_create_article(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/articles",
        json={"topic": "AI란 무엇인가?"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["topic"] == "AI란 무엇인가?"
    assert body["data"]["status"] == "draft"
    assert body["data"]["slug"] != ""


async def test_create_article_with_title(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/articles",
        json={"topic": "AI 기초", "title": "커스텀 제목", "category": "AI/ML"},
    )

    body = response.json()
    assert body["data"]["title"] == "커스텀 제목"
    assert body["data"]["category"] == "AI/ML"


async def test_create_article_validation_error(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/articles",
        json={"topic": "X"},
    )
    assert response.status_code == 422


async def test_list_articles_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/articles")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["total"] == 0
    assert body["data"]["items"] == []


async def test_list_articles_with_data(client: AsyncClient) -> None:
    await client.post("/api/v1/articles", json={"topic": "주제 하나"})
    await client.post("/api/v1/articles", json={"topic": "주제 둘"})

    response = await client.get("/api/v1/articles")
    body = response.json()
    assert body["data"]["total"] == 2
    assert len(body["data"]["items"]) == 2


async def test_get_article(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/v1/articles", json={"topic": "조회 테스트"}
    )
    article_id = create_resp.json()["data"]["id"]

    response = await client.get(f"/api/v1/articles/{article_id}")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == article_id


async def test_get_article_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/articles/9999")
    assert response.status_code == 404


async def test_update_article(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/v1/articles", json={"topic": "수정 테스트"}
    )
    article_id = create_resp.json()["data"]["id"]

    response = await client.patch(
        f"/api/v1/articles/{article_id}",
        json={"title": "수정된 제목"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "수정된 제목"


async def test_delete_article(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/v1/articles", json={"topic": "삭제 테스트"}
    )
    article_id = create_resp.json()["data"]["id"]

    response = await client.delete(f"/api/v1/articles/{article_id}")
    assert response.status_code == 200
    assert response.json()["data"]["deleted"] is True

    get_resp = await client.get(f"/api/v1/articles/{article_id}")
    assert get_resp.status_code == 404


async def test_get_content_success(client: AsyncClient) -> None:
    mock_fm = MagicMock()
    mock_fm.read_text.return_value = "# 테스트 콘텐츠\n\n본문입니다."
    client._transport.app.dependency_overrides[get_file_manager] = lambda: mock_fm

    create_resp = await client.post(
        "/api/v1/articles", json={"topic": "콘텐츠 테스트"}
    )
    article_id = create_resp.json()["data"]["id"]

    response = await client.get(f"/api/v1/articles/{article_id}/content")
    assert response.status_code == 200
    assert "테스트 콘텐츠" in response.text
    assert response.headers["content-type"].startswith("text/markdown")


async def test_get_content_not_generated(client: AsyncClient) -> None:
    mock_fm = MagicMock()
    mock_fm.read_text.return_value = None
    client._transport.app.dependency_overrides[get_file_manager] = lambda: mock_fm

    create_resp = await client.post(
        "/api/v1/articles", json={"topic": "미생성 콘텐츠"}
    )
    article_id = create_resp.json()["data"]["id"]

    response = await client.get(f"/api/v1/articles/{article_id}/content")
    assert response.status_code == 404


async def test_get_content_article_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/articles/9999/content")
    assert response.status_code == 404


# --- update_article not found (lines 74-76) ---


async def test_update_article_not_found(client: AsyncClient) -> None:
    response = await client.patch(
        "/api/v1/articles/9999",
        json={"title": "존재하지 않는 글"},
    )
    assert response.status_code == 404


# --- delete_article not found (lines 227-229) ---


async def test_delete_article_not_found(client: AsyncClient) -> None:
    response = await client.delete("/api/v1/articles/9999")
    assert response.status_code == 404


# --- update_article_content (PUT /{id}/content, lines 104-115) ---


async def test_update_content_success(client: AsyncClient) -> None:
    mock_fm = MagicMock()
    mock_fm.read_text.return_value = "기존 콘텐츠"
    _override_fm(client, mock_fm)

    article_id = await _create_article(client, "콘텐츠 수정 테스트")

    response = await client.put(
        f"/api/v1/articles/{article_id}/content",
        json={"content": "# 새 콘텐츠\n\n본문입니다."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["word_count"] > 0

    mock_fm.backup_content.assert_called_once()
    mock_fm.write_text.assert_called_once()


async def test_update_content_article_not_found(client: AsyncClient) -> None:
    response = await client.put(
        "/api/v1/articles/9999/content",
        json={"content": "아무 내용"},
    )
    assert response.status_code == 404


async def test_update_content_empty_body(client: AsyncClient) -> None:
    mock_fm = MagicMock()
    _override_fm(client, mock_fm)

    article_id = await _create_article(client, "빈 콘텐츠 테스트")

    response = await client.put(
        f"/api/v1/articles/{article_id}/content",
        json={"content": ""},
    )
    assert response.status_code == 400


async def test_update_content_missing_content_key(client: AsyncClient) -> None:
    mock_fm = MagicMock()
    _override_fm(client, mock_fm)

    article_id = await _create_article(client, "키 누락 테스트")

    response = await client.put(
        f"/api/v1/articles/{article_id}/content",
        json={"other": "value"},
    )
    assert response.status_code == 400


# --- get_article_html (GET /{id}/html, lines 124-130) ---


async def test_get_html_success(client: AsyncClient) -> None:
    mock_fm = MagicMock()
    mock_fm.read_text.return_value = "<h1>제목</h1><p>본문</p>"
    _override_fm(client, mock_fm)

    article_id = await _create_article(client, "HTML 테스트")

    response = await client.get(f"/api/v1/articles/{article_id}/html")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "<h1>제목</h1>" in body["data"]


async def test_get_html_not_generated(client: AsyncClient) -> None:
    mock_fm = MagicMock()
    mock_fm.read_text.return_value = None
    _override_fm(client, mock_fm)

    article_id = await _create_article(client, "HTML 미생성 테스트")

    response = await client.get(f"/api/v1/articles/{article_id}/html")
    assert response.status_code == 404


async def test_get_html_article_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/articles/9999/html")
    assert response.status_code == 404


# --- get_publish_kit (GET /{id}/publish-kit, lines 140-168) ---


async def test_get_publish_kit_success(client: AsyncClient) -> None:
    mock_fm = MagicMock()
    mock_fm.read_json.return_value = {
        "seo_keywords": ["AI", "머신러닝"],
        "category": "기술",
    }
    mock_fm.read_text.side_effect = lambda slug, filename: {
        "final.md": "# 제목\n\n본문 내용입니다.",
        "tistory.html": "<h1>제목</h1>",
    }.get(filename)
    mock_fm.list_images.return_value = ["thumb.png", "diagram.svg"]
    mock_fm.list_diagrams.return_value = ["flow.mmd"]

    def _read_text_for_diagrams(slug: str, filename: str) -> str | None:
        mapping = {
            "final.md": "# 제목\n\n본문 내용입니다.",
            "tistory.html": "<h1>제목</h1>",
            "diagrams/flow.mmd": "graph TD\n  A-->B",
        }
        return mapping.get(filename)

    mock_fm.read_text.side_effect = _read_text_for_diagrams
    _override_fm(client, mock_fm)

    article_id = await _create_article(client, "퍼블리시킷 테스트")

    response = await client.get(f"/api/v1/articles/{article_id}/publish-kit")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True

    kit = body["data"]
    assert kit["tags"] == ["AI", "머신러닝"]
    assert kit["markdown"] is not None
    assert kit["html"] == "<h1>제목</h1>"
    assert len(kit["images"]) == 2
    assert kit["images"][0]["name"] == "thumb.png"
    assert f"/api/v1/articles/{article_id}/images/thumb.png" in kit["images"][0]["url"]
    assert len(kit["diagrams"]) == 1
    assert kit["diagrams"][0]["name"] == "flow.mmd"
    assert kit["word_count"] > 0
    assert kit["status"] == "draft"


async def test_get_publish_kit_no_meta(client: AsyncClient) -> None:
    """meta.json이 없는 경우"""
    mock_fm = MagicMock()
    mock_fm.read_json.return_value = None
    mock_fm.read_text.return_value = None
    mock_fm.list_images.return_value = []
    mock_fm.list_diagrams.return_value = []
    _override_fm(client, mock_fm)

    article_id = await _create_article(client, "메타 없는 퍼블리시킷")

    response = await client.get(f"/api/v1/articles/{article_id}/publish-kit")
    assert response.status_code == 200
    kit = response.json()["data"]
    assert kit["tags"] == []
    assert kit["markdown"] is None
    assert kit["word_count"] == 0


async def test_get_publish_kit_article_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/articles/9999/publish-kit")
    assert response.status_code == 404


# --- list_article_images (GET /{id}/images, lines 190-194) ---


async def test_list_images_success(client: AsyncClient) -> None:
    mock_fm = MagicMock()
    mock_fm.list_images.return_value = ["img1.png", "img2.jpg"]
    _override_fm(client, mock_fm)

    article_id = await _create_article(client, "이미지 목록 테스트")

    response = await client.get(f"/api/v1/articles/{article_id}/images")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] == ["img1.png", "img2.jpg"]


async def test_list_images_empty(client: AsyncClient) -> None:
    mock_fm = MagicMock()
    mock_fm.list_images.return_value = []
    _override_fm(client, mock_fm)

    article_id = await _create_article(client, "이미지 없는 글")

    response = await client.get(f"/api/v1/articles/{article_id}/images")
    assert response.status_code == 200
    assert response.json()["data"] == []


async def test_list_images_article_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/articles/9999/images")
    assert response.status_code == 404


# --- get_article_image (GET /{id}/images/{filename}, lines 204-214) ---


async def test_get_image_success(client: AsyncClient, tmp_path: Path) -> None:
    mock_fm = MagicMock()
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    image_file = images_dir / "test.png"
    image_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    mock_fm.images_dir.return_value = images_dir
    _override_fm(client, mock_fm)

    article_id = await _create_article(client, "이미지 조회 테스트")

    response = await client.get(f"/api/v1/articles/{article_id}/images/test.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["cache-control"] == "public, max-age=3600"


async def test_get_image_not_found(client: AsyncClient, tmp_path: Path) -> None:
    mock_fm = MagicMock()
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    mock_fm.images_dir.return_value = images_dir
    _override_fm(client, mock_fm)

    article_id = await _create_article(client, "이미지 미존재 테스트")

    response = await client.get(
        f"/api/v1/articles/{article_id}/images/nonexistent.png"
    )
    assert response.status_code == 404


async def test_get_image_article_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/articles/9999/images/test.png")
    assert response.status_code == 404


async def test_get_image_path_traversal(client: AsyncClient, tmp_path: Path) -> None:
    """경로 순회 공격 방어 확인"""
    mock_fm = MagicMock()
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    mock_fm.images_dir.return_value = images_dir
    _override_fm(client, mock_fm)

    article_id = await _create_article(client, "경로 순회 테스트")

    response = await client.get(
        f"/api/v1/articles/{article_id}/images/..%2F..%2Fetc%2Fpasswd"
    )
    assert response.status_code == 404


# --- list_versions (GET /{id}/versions, lines 238-242) ---


async def test_list_versions_success(client: AsyncClient) -> None:
    mock_fm = MagicMock()
    mock_fm.list_versions.return_value = [
        {
            "version_id": "1716000000000",
            "timestamp": "2026-05-18 12:00:00",
            "size": 500,
            "word_count": 300,
        },
    ]
    _override_fm(client, mock_fm)

    article_id = await _create_article(client, "버전 목록 테스트")

    response = await client.get(f"/api/v1/articles/{article_id}/versions")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]) == 1
    assert body["data"][0]["version_id"] == "1716000000000"


async def test_list_versions_empty(client: AsyncClient) -> None:
    mock_fm = MagicMock()
    mock_fm.list_versions.return_value = []
    _override_fm(client, mock_fm)

    article_id = await _create_article(client, "버전 없는 글")

    response = await client.get(f"/api/v1/articles/{article_id}/versions")
    assert response.status_code == 200
    assert response.json()["data"] == []


async def test_list_versions_article_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/articles/9999/versions")
    assert response.status_code == 404


# --- get_version_content (GET /{id}/versions/{version_id}, lines 252-258) ---


async def test_get_version_content_success(client: AsyncClient) -> None:
    mock_fm = MagicMock()
    mock_fm.get_version_content.return_value = "# 이전 버전 콘텐츠"
    _override_fm(client, mock_fm)

    article_id = await _create_article(client, "버전 콘텐츠 테스트")

    response = await client.get(
        f"/api/v1/articles/{article_id}/versions/1716000000000"
    )
    assert response.status_code == 200
    assert "이전 버전 콘텐츠" in response.text
    assert response.headers["content-type"].startswith("text/markdown")


async def test_get_version_content_not_found(client: AsyncClient) -> None:
    mock_fm = MagicMock()
    mock_fm.get_version_content.return_value = None
    _override_fm(client, mock_fm)

    article_id = await _create_article(client, "없는 버전 테스트")

    response = await client.get(
        f"/api/v1/articles/{article_id}/versions/nonexistent"
    )
    assert response.status_code == 404


async def test_get_version_content_article_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/articles/9999/versions/123")
    assert response.status_code == 404


# --- restore_version (POST /{id}/versions/{version_id}/restore, lines 268-277) ---


async def test_restore_version_success(client: AsyncClient) -> None:
    mock_fm = MagicMock()
    mock_fm.restore_version.return_value = True
    mock_fm.read_text.return_value = "# 복원된 콘텐츠 내용"
    _override_fm(client, mock_fm)

    article_id = await _create_article(client, "버전 복원 테스트")

    response = await client.post(
        f"/api/v1/articles/{article_id}/versions/1716000000000/restore"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["restored"] is True
    assert body["data"]["word_count"] > 0


async def test_restore_version_not_found(client: AsyncClient) -> None:
    mock_fm = MagicMock()
    mock_fm.restore_version.return_value = False
    _override_fm(client, mock_fm)

    article_id = await _create_article(client, "없는 버전 복원")

    response = await client.post(
        f"/api/v1/articles/{article_id}/versions/nonexistent/restore"
    )
    assert response.status_code == 404


async def test_restore_version_article_not_found(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/articles/9999/versions/123/restore"
    )
    assert response.status_code == 404


async def test_restore_version_no_content_after_restore(
    client: AsyncClient,
) -> None:
    """복원 후 final.md가 없는 경우 word_count=0"""
    mock_fm = MagicMock()
    mock_fm.restore_version.return_value = True
    mock_fm.read_text.return_value = None
    _override_fm(client, mock_fm)

    article_id = await _create_article(client, "빈 복원 테스트")

    response = await client.post(
        f"/api/v1/articles/{article_id}/versions/1716000000000/restore"
    )
    assert response.status_code == 200
    assert response.json()["data"]["word_count"] == 0


# --- save_to_obsidian (POST /{id}/save-obsidian, lines 286-297) ---


async def test_save_obsidian_success(client: AsyncClient) -> None:
    mock_fm = MagicMock()
    _override_fm(client, mock_fm)

    article_id = await _create_article(client, "옵시디언 저장 테스트")

    mock_obsidian = MagicMock()
    mock_obsidian.save_article.return_value = {
        "success": True,
        "path": "/vault/test.md",
    }

    with patch(
        "app.services.obsidian_service.ObsidianService",
        return_value=mock_obsidian,
    ):
        response = await client.post(
            f"/api/v1/articles/{article_id}/save-obsidian"
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["path"] == "/vault/test.md"


async def test_save_obsidian_failure(client: AsyncClient) -> None:
    mock_fm = MagicMock()
    _override_fm(client, mock_fm)

    article_id = await _create_article(client, "옵시디언 실패 테스트")

    mock_obsidian = MagicMock()
    mock_obsidian.save_article.return_value = {
        "success": False,
        "error": "vault 경로를 찾을 수 없습니다",
    }

    with patch(
        "app.services.obsidian_service.ObsidianService",
        return_value=mock_obsidian,
    ):
        response = await client.post(
            f"/api/v1/articles/{article_id}/save-obsidian"
        )

    assert response.status_code == 400


async def test_save_obsidian_article_not_found(client: AsyncClient) -> None:
    response = await client.post("/api/v1/articles/9999/save-obsidian")
    assert response.status_code == 404


# --- list_articles pagination (line 42) ---


async def test_list_articles_pagination(client: AsyncClient) -> None:
    for i in range(5):
        await client.post(
            "/api/v1/articles", json={"topic": f"페이지 테스트 {i + 1}번"}
        )

    response = await client.get("/api/v1/articles?page=2&limit=2")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["total"] == 5
    assert body["data"]["page"] == 2
    assert body["data"]["limit"] == 2
    assert len(body["data"]["items"]) == 2

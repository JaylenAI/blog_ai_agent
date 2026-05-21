from httpx import AsyncClient


async def test_create_article(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/articles",
        json={"topic": "AI란 무엇인가?"},
    )

    assert response.status_code == 200
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

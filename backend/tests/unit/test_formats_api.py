import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_list_formats(client: AsyncClient) -> None:
    res = await client.get("/api/v1/formats")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 7
    first = body["data"][0]
    assert "id" in first
    assert "name" in first
    assert "section_count_min" in first
    assert "char_count_standard" in first


@pytest.mark.anyio
async def test_suggest_format(client: AsyncClient) -> None:
    res = await client.get("/api/v1/formats/suggest", params={"topic": "Docker 설치 따라하기"})
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert len(body["data"]) >= 1
    assert body["data"][0]["format_id"] == "tutorial"


@pytest.mark.anyio
async def test_suggest_empty_topic(client: AsyncClient) -> None:
    res = await client.get("/api/v1/formats/suggest", params={"topic": ""})
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert len(body["data"]) >= 1


@pytest.mark.anyio
async def test_get_format_detail(client: AsyncClient) -> None:
    res = await client.get("/api/v1/formats/concept")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["id"] == "concept"
    assert "structure" in body["data"]
    assert "elements" in body["data"]
    assert "validation" in body["data"]


@pytest.mark.anyio
async def test_get_format_not_found(client: AsyncClient) -> None:
    res = await client.get("/api/v1/formats/nonexistent_xyz")
    assert res.status_code == 404

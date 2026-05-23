"""API 통합 테스트 — 실제 DB + mock Claude/FileManager로 REST 엔드포인트 검증."""

from httpx import AsyncClient

from app.dependencies import get_claude_client, get_file_manager

from .conftest import build_mock_claude, build_mock_file_manager


def _override_deps(
    client: AsyncClient, *, full_pipeline: bool = False
) -> None:
    mock_claude = build_mock_claude(full_pipeline=full_pipeline)
    mock_fm = build_mock_file_manager(with_content=full_pipeline)
    app = client._transport.app
    app.dependency_overrides[get_claude_client] = lambda: mock_claude
    app.dependency_overrides[get_file_manager] = lambda: mock_fm


# ── Articles + Pipeline 통합 흐름 ──


async def test_full_flow_gate_one_pause(integration_client: AsyncClient) -> None:
    _override_deps(integration_client)

    create_resp = await integration_client.post(
        "/api/v1/articles", json={"topic": "LLM이란 무엇인가"}
    )
    assert create_resp.status_code == 201
    article_id = create_resp.json()["data"]["id"]

    start_resp = await integration_client.post(
        "/api/v1/pipeline/start", json={"article_id": article_id}
    )
    assert start_resp.status_code == 200
    body = start_resp.json()
    assert body["success"] is True

    events = body["data"]["events"]
    event_types = [e["event_type"] for e in events]
    assert "stage_start" in event_types
    assert "stage_complete" in event_types
    assert "gate_pending" in event_types
    assert "pipeline_complete" not in event_types

    run_id = body["data"]["run_id"]
    assert isinstance(run_id, int)

    run_resp = await integration_client.get(f"/api/v1/pipeline/runs/{run_id}")
    assert run_resp.status_code == 200
    run_data = run_resp.json()["data"]
    assert run_data["status"] == "paused"
    assert run_data["current_stage"] == "gate_one"


async def test_full_flow_reject_at_gate(integration_client: AsyncClient) -> None:
    _override_deps(integration_client)

    create_resp = await integration_client.post(
        "/api/v1/articles", json={"topic": "거부 테스트"}
    )
    article_id = create_resp.json()["data"]["id"]

    start_resp = await integration_client.post(
        "/api/v1/pipeline/start", json={"article_id": article_id}
    )
    run_id = start_resp.json()["data"]["run_id"]

    reject_resp = await integration_client.post(
        f"/api/v1/pipeline/runs/{run_id}/reject"
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["data"]["status"] == "cancelled"

    run_resp = await integration_client.get(f"/api/v1/pipeline/runs/{run_id}")
    assert run_resp.json()["data"]["status"] == "cancelled"


async def test_reject_already_cancelled(integration_client: AsyncClient) -> None:
    _override_deps(integration_client)

    create_resp = await integration_client.post(
        "/api/v1/articles", json={"topic": "이중 거부 테스트"}
    )
    article_id = create_resp.json()["data"]["id"]

    start_resp = await integration_client.post(
        "/api/v1/pipeline/start", json={"article_id": article_id}
    )
    run_id = start_resp.json()["data"]["run_id"]

    await integration_client.post(f"/api/v1/pipeline/runs/{run_id}/reject")

    second_reject = await integration_client.post(
        f"/api/v1/pipeline/runs/{run_id}/reject"
    )
    assert second_reject.status_code == 400


async def test_pipeline_start_nonexistent_article(integration_client: AsyncClient) -> None:
    _override_deps(integration_client)

    resp = await integration_client.post(
        "/api/v1/pipeline/start", json={"article_id": 99999}
    )
    body = resp.json()
    assert body["success"] is False


async def test_pipeline_claude_error_marks_failed(integration_client: AsyncClient) -> None:
    mock_claude = build_mock_claude()
    mock_claude.run_json.side_effect = RuntimeError("subprocess failed")
    mock_fm = build_mock_file_manager()
    app = integration_client._transport.app
    app.dependency_overrides[get_claude_client] = lambda: mock_claude
    app.dependency_overrides[get_file_manager] = lambda: mock_fm

    create_resp = await integration_client.post(
        "/api/v1/articles", json={"topic": "에러 테스트"}
    )
    article_id = create_resp.json()["data"]["id"]

    start_resp = await integration_client.post(
        "/api/v1/pipeline/start", json={"article_id": article_id}
    )
    body = start_resp.json()
    assert body["success"] is False

    events = body["data"]["events"]
    assert any(e["event_type"] == "stage_error" for e in events)


# ── Validations Endpoint ──


async def test_validations_endpoint_empty(integration_client: AsyncClient) -> None:
    _override_deps(integration_client)

    create_resp = await integration_client.post(
        "/api/v1/articles", json={"topic": "검증 테스트"}
    )
    article_id = create_resp.json()["data"]["id"]

    start_resp = await integration_client.post(
        "/api/v1/pipeline/start", json={"article_id": article_id}
    )
    run_id = start_resp.json()["data"]["run_id"]

    val_resp = await integration_client.get(
        f"/api/v1/pipeline/runs/{run_id}/validations"
    )
    assert val_resp.status_code == 200
    val_body = val_resp.json()
    assert val_body["success"] is True
    assert val_body["data"]["summary"]["total"] == 0


async def test_validations_endpoint_with_data(integration_client: AsyncClient) -> None:
    _override_deps(integration_client, full_pipeline=True)

    create_resp = await integration_client.post(
        "/api/v1/articles", json={"topic": "검증 데이터 테스트"}
    )
    article_id = create_resp.json()["data"]["id"]

    start_resp = await integration_client.post(
        "/api/v1/pipeline/start",
        json={"article_id": article_id, "auto_gate_one": True},
    )
    body = start_resp.json()
    run_id = body["data"]["run_id"]

    val_resp = await integration_client.get(
        f"/api/v1/pipeline/runs/{run_id}/validations"
    )
    val_body = val_resp.json()
    assert val_body["success"] is True

    summary = val_body["data"]["summary"]
    assert summary["total"] > 0
    assert "score" in summary


# ── Article CRUD ──


async def test_article_list_and_get(integration_client: AsyncClient) -> None:
    await integration_client.post(
        "/api/v1/articles", json={"topic": "목록 테스트 1"}
    )
    await integration_client.post(
        "/api/v1/articles", json={"topic": "목록 테스트 2"}
    )

    list_resp = await integration_client.get("/api/v1/articles")
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["data"]["total"] >= 2

    article_id = body["data"]["items"][0]["id"]
    get_resp = await integration_client.get(f"/api/v1/articles/{article_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["id"] == article_id


async def test_article_not_found(integration_client: AsyncClient) -> None:
    resp = await integration_client.get("/api/v1/articles/99999")
    assert resp.status_code == 404


# ── Run Not Found ──


async def test_get_run_not_found(integration_client: AsyncClient) -> None:
    _override_deps(integration_client)

    resp = await integration_client.get("/api/v1/pipeline/runs/99999")
    assert resp.status_code == 404


async def test_approve_run_not_found(integration_client: AsyncClient) -> None:
    _override_deps(integration_client)

    resp = await integration_client.post("/api/v1/pipeline/runs/99999/approve")
    body = resp.json()
    assert body["success"] is False

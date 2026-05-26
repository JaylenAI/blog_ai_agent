from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, HttpUrl

from app.schemas.common import ApiResponse
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

WEBHOOKS_FILE = Path(__file__).resolve().parents[4] / "data" / "webhooks.json"


def _load_webhooks() -> list[dict]:
    if WEBHOOKS_FILE.exists():
        return json.loads(WEBHOOKS_FILE.read_text(encoding="utf-8"))
    return []


def _save_webhooks(hooks: list[dict]) -> None:
    WEBHOOKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    WEBHOOKS_FILE.write_text(
        json.dumps(hooks, ensure_ascii=False, indent=2), encoding="utf-8"
    )


class WebhookCreate(BaseModel):
    url: HttpUrl
    events: list[str] = ["pipeline_complete", "gate_pending", "pipeline_error"]
    name: str = ""
    active: bool = True


class WebhookResponse(BaseModel):
    id: int
    url: str
    events: list[str]
    name: str
    active: bool


@router.get("")
async def list_webhooks() -> ApiResponse[list[WebhookResponse]]:
    hooks = _load_webhooks()
    return ApiResponse(
        success=True,
        data=[WebhookResponse(id=i, **h) for i, h in enumerate(hooks)],
    )


@router.post("")
async def create_webhook(data: WebhookCreate) -> ApiResponse[WebhookResponse]:
    hooks = _load_webhooks()
    hook = {
        "url": str(data.url),
        "events": data.events,
        "name": data.name or f"webhook-{len(hooks)}",
        "active": data.active,
    }
    hooks.append(hook)
    _save_webhooks(hooks)

    return ApiResponse(
        success=True,
        data=WebhookResponse(id=len(hooks) - 1, **hook),
    )


@router.delete("/{hook_id}")
async def delete_webhook(hook_id: int) -> ApiResponse[dict]:
    hooks = _load_webhooks()
    if hook_id < 0 or hook_id >= len(hooks):
        return ApiResponse(success=False, error="Webhook을 찾을 수 없습니다")
    removed = hooks.pop(hook_id)
    _save_webhooks(hooks)
    return ApiResponse(success=True, data={"removed": removed["name"]})


@router.patch("/{hook_id}/toggle")
async def toggle_webhook(hook_id: int) -> ApiResponse[WebhookResponse]:
    hooks = _load_webhooks()
    if hook_id < 0 or hook_id >= len(hooks):
        return ApiResponse(success=False, error="Webhook을 찾을 수 없습니다")
    hooks[hook_id]["active"] = not hooks[hook_id]["active"]
    _save_webhooks(hooks)
    return ApiResponse(
        success=True,
        data=WebhookResponse(id=hook_id, **hooks[hook_id]),
    )

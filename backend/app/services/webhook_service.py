from __future__ import annotations

import json
from pathlib import Path

import httpx

from app.utils.logger import get_logger

logger = get_logger(__name__)

WEBHOOKS_FILE = Path(__file__).resolve().parents[3] / "data" / "webhooks.json"


def _load_webhooks() -> list[dict]:
    if WEBHOOKS_FILE.exists():
        return json.loads(WEBHOOKS_FILE.read_text(encoding="utf-8"))
    return []


async def dispatch_webhook(event_type: str, payload: dict) -> None:
    hooks = _load_webhooks()
    active = [h for h in hooks if h.get("active") and event_type in h.get("events", [])]

    if not active:
        return

    body = {"event": event_type, "data": payload}

    async with httpx.AsyncClient(timeout=10) as client:
        for hook in active:
            try:
                resp = await client.post(
                    hook["url"],
                    json=body,
                    headers={"Content-Type": "application/json"},
                )
                logger.info(
                    "Webhook 전송 완료: %s → %s (status=%d)",
                    event_type,
                    hook.get("name", hook["url"]),
                    resp.status_code,
                )
            except Exception as e:
                logger.warning(
                    "Webhook 전송 실패: %s → %s: %s",
                    event_type,
                    hook.get("name", hook["url"]),
                    e,
                )

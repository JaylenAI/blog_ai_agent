from __future__ import annotations

import base64
from urllib.parse import urljoin

import httpx

from app.publishers.base import PublisherAdapter
from app.utils.logger import get_logger

logger = get_logger(__name__)


class WordPressPublisher(PublisherAdapter):
    def __init__(
        self,
        site_url: str,
        username: str,
        app_password: str,
    ) -> None:
        self._site_url = site_url.rstrip("/")
        self._username = username
        self._app_password = app_password

    @property
    def platform_name(self) -> str:
        return "wordpress"

    def _auth_header(self) -> dict[str, str]:
        cred = base64.b64encode(
            f"{self._username}:{self._app_password}".encode()
        ).decode()
        return {"Authorization": f"Basic {cred}"}

    async def publish(
        self,
        title: str,
        html_content: str,
        *,
        category: str = "",
        tags: list[str] | None = None,
        status: str = "draft",
        **kwargs: object,
    ) -> dict:
        api_url = urljoin(self._site_url + "/", "wp-json/wp/v2/posts")
        payload: dict = {
            "title": title,
            "content": html_content,
            "status": status,
        }

        if tags:
            tag_ids = await self._resolve_tags(tags)
            if tag_ids:
                payload["tags"] = tag_ids

        if category:
            cat_ids = await self._resolve_categories([category])
            if cat_ids:
                payload["categories"] = cat_ids

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                api_url,
                json=payload,
                headers=self._auth_header(),
            )
            resp.raise_for_status()
            data = resp.json()

        post_url = data.get("link", "")
        logger.info("WordPress 게시 완료: %s (id=%s)", post_url, data.get("id"))

        return {
            "success": True,
            "platform": "wordpress",
            "post_id": data.get("id"),
            "url": post_url,
        }

    async def _resolve_tags(self, tag_names: list[str]) -> list[int]:
        api_url = urljoin(self._site_url + "/", "wp-json/wp/v2/tags")
        tag_ids: list[int] = []

        async with httpx.AsyncClient(timeout=15) as client:
            for name in tag_names[:10]:
                resp = await client.get(
                    api_url,
                    params={"search": name},
                    headers=self._auth_header(),
                )
                if resp.status_code == 200:
                    results = resp.json()
                    if results:
                        tag_ids.append(results[0]["id"])
                    else:
                        create_resp = await client.post(
                            api_url,
                            json={"name": name},
                            headers=self._auth_header(),
                        )
                        if create_resp.status_code == 201:
                            tag_ids.append(create_resp.json()["id"])

        return tag_ids

    async def _resolve_categories(self, names: list[str]) -> list[int]:
        api_url = urljoin(self._site_url + "/", "wp-json/wp/v2/categories")
        cat_ids: list[int] = []

        async with httpx.AsyncClient(timeout=15) as client:
            for name in names:
                resp = await client.get(
                    api_url,
                    params={"search": name},
                    headers=self._auth_header(),
                )
                if resp.status_code == 200 and resp.json():
                    cat_ids.append(resp.json()[0]["id"])

        return cat_ids

from abc import ABC, abstractmethod


class PublisherAdapter(ABC):
    @abstractmethod
    async def publish(
        self,
        title: str,
        html_content: str,
        *,
        category: str = "",
        tags: list[str] | None = None,
        **kwargs: object,
    ) -> dict:
        ...

    @property
    @abstractmethod
    def platform_name(self) -> str:
        ...

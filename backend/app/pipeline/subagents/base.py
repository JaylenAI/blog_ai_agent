from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.claude.client import ClaudeClient
from app.claude.prompts.base import PromptTemplate
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class Reference:
    url: str
    title: str
    summary: str
    source_type: str
    relevance_score: float = 0.8


class LibrarianSubagent(ABC):
    def __init__(self, claude: ClaudeClient) -> None:
        self._claude = claude

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def source_type(self) -> str: ...

    @abstractmethod
    def _get_prompt(self) -> PromptTemplate: ...

    async def search(
        self, topic: str, queries: list[str]
    ) -> list[Reference]:
        prompt = self._get_prompt().render(
            topic=topic, queries="\n".join(f"- {q}" for q in queries)
        )

        try:
            result = await self._claude.run_json(
                prompt,
                allowed_tools=["WebSearch", "WebFetch"],
            )
        except (RuntimeError, ValueError) as e:
            logger.warning("Librarian %s 실패: %s", self.name, e)
            return []

        raw_refs = result.get("references", [])
        refs = []
        for r in raw_refs:
            if not all(k in r for k in ("url", "title", "summary")):
                continue
            refs.append(
                Reference(
                    url=r["url"],
                    title=r["title"],
                    summary=r["summary"],
                    source_type=self.source_type,
                    relevance_score=float(r.get("relevance_score", 0.8)),
                )
            )

        logger.info("Librarian %s: %d건 수집", self.name, len(refs))
        return refs

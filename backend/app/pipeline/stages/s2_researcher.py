import asyncio

from app.claude.client import ClaudeClient
from app.pipeline.base import Stage, StageInput, StageOutput
from app.pipeline.subagents.base import Reference
from app.pipeline.subagents.librarian_blog_en import BlogEnLibrarian
from app.pipeline.subagents.librarian_blog_kr import BlogKrLibrarian
from app.pipeline.subagents.librarian_github import GithubLibrarian
from app.pipeline.subagents.librarian_official import OfficialLibrarian
from app.utils.file_manager import FileManager
from app.utils.logger import get_logger

logger = get_logger(__name__)

SOURCE_TYPES = ("official", "github", "blog_en", "blog_kr")


class ResearcherStage(Stage):
    def __init__(self, claude: ClaudeClient, file_manager: FileManager) -> None:
        self._fm = file_manager
        self._librarians = [
            OfficialLibrarian(claude),
            GithubLibrarian(claude),
            BlogEnLibrarian(claude),
            BlogKrLibrarian(claude),
        ]

    @property
    def name(self) -> str:
        return "researcher"

    async def execute(self, stage_input: StageInput) -> StageOutput:
        queries = stage_input.data.get("search_queries", [])
        if not queries:
            return StageOutput(
                stage_name=self.name,
                success=False,
                error="search_queries가 비어 있습니다 (Router 출력 확인 필요)",
            )

        results = await asyncio.gather(
            *[lib.search(stage_input.topic, queries) for lib in self._librarians],
            return_exceptions=True,
        )

        all_refs: list[Reference] = []
        for result in results:
            if isinstance(result, BaseException):
                logger.warning("Librarian 실패: %s", result)
                continue
            all_refs.extend(result)

        unique_refs = _deduplicate(all_refs)
        unique_refs.sort(key=lambda r: r.relevance_score, reverse=True)

        refs_data = [
            {
                "url": r.url,
                "title": r.title,
                "summary": r.summary,
                "source_type": r.source_type,
                "relevance_score": r.relevance_score,
            }
            for r in unique_refs
        ]
        self._fm.write_json(stage_input.slug, "references.json", refs_data)

        if len(unique_refs) < 3:
            return StageOutput(
                stage_name=self.name,
                success=False,
                error=f"참고자료가 {len(unique_refs)}건으로 최소 기준(3건) 미달",
            )

        by_source = {
            src: len([r for r in unique_refs if r.source_type == src])
            for src in SOURCE_TYPES
        }

        logger.info(
            "Researcher 완료: 총 %d건 (official=%d, github=%d, en=%d, kr=%d)",
            len(unique_refs),
            by_source["official"],
            by_source["github"],
            by_source["blog_en"],
            by_source["blog_kr"],
        )

        return StageOutput(
            stage_name=self.name,
            success=True,
            data={
                "references": refs_data,
                "total_count": len(unique_refs),
                "by_source": by_source,
            },
        )


def _deduplicate(refs: list[Reference]) -> list[Reference]:
    seen: set[str] = set()
    unique: list[Reference] = []
    for ref in refs:
        if ref.url not in seen:
            seen.add(ref.url)
            unique.append(ref)
    return unique

from collections.abc import Sequence

from app.db.repositories.article_repo import ArticleRepository
from app.models.article import Article, ArticleStatus
from app.schemas.article import ArticleCreate, ArticleUpdate
from app.utils.file_manager import FileManager
from app.utils.slug import generate_slug


class ArticleService:
    def __init__(self, repo: ArticleRepository, file_manager: FileManager | None = None) -> None:
        self._repo = repo
        self._fm = file_manager

    async def create(self, data: ArticleCreate) -> Article:
        slug = generate_slug(data.topic)

        existing = await self._repo.find_by_slug(slug)
        if existing:
            count = await self._repo.count()
            slug = f"{slug}-{count + 1}"

        article = Article(
            slug=slug,
            title=data.title or data.topic,
            topic=data.topic,
            category=data.category,
            format_id=data.format_id,
            status=ArticleStatus.DRAFT,
            content_path=f".sisyphus/{slug}",
        )
        return await self._repo.create(article)

    async def get_by_id(self, article_id: int) -> Article | None:
        return await self._repo.find_by_id(article_id)

    async def get_by_slug(self, slug: str) -> Article | None:
        return await self._repo.find_by_slug(slug)

    async def list_all(
        self, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Article], int]:
        articles = await self._repo.find_all(offset=offset, limit=limit)
        total = await self._repo.count()
        return articles, total

    async def update(
        self, article_id: int, data: ArticleUpdate
    ) -> Article | None:
        article = await self._repo.find_by_id(article_id)
        if not article:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(article, field, value)

        await self._repo._session.flush()
        await self._repo._session.refresh(article)
        return article

    async def delete(self, article_id: int) -> bool:
        article = await self._repo.find_by_id(article_id)
        if not article:
            return False
        if self._fm:
            self._fm.delete_article_dir(article.slug)
        await self._repo.delete(article)
        return True

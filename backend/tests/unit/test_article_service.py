from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.article_repo import ArticleRepository
from app.models.article import ArticleStatus
from app.schemas.article import ArticleCreate, ArticleUpdate
from app.services.article_service import ArticleService


def _make_service(db_session: AsyncSession) -> ArticleService:
    return ArticleService(ArticleRepository(db_session))


async def test_create_article(db_session: AsyncSession) -> None:
    service = _make_service(db_session)
    article = await service.create(ArticleCreate(topic="AI란 무엇인가?"))

    assert article.id is not None
    assert article.topic == "AI란 무엇인가?"
    assert article.title == "AI란 무엇인가?"
    assert article.status == ArticleStatus.DRAFT
    assert article.slug != ""
    assert ".sisyphus/" in article.content_path


async def test_create_with_custom_title(db_session: AsyncSession) -> None:
    service = _make_service(db_session)
    article = await service.create(
        ArticleCreate(topic="AI 기초", title="나만의 제목")
    )

    assert article.title == "나만의 제목"


async def test_duplicate_slug_gets_suffix(db_session: AsyncSession) -> None:
    service = _make_service(db_session)
    a1 = await service.create(ArticleCreate(topic="같은 주제"))
    a2 = await service.create(ArticleCreate(topic="같은 주제"))

    assert a1.slug != a2.slug


async def test_get_by_id(db_session: AsyncSession) -> None:
    service = _make_service(db_session)
    created = await service.create(ArticleCreate(topic="조회 테스트"))

    found = await service.get_by_id(created.id)
    assert found is not None
    assert found.id == created.id


async def test_get_nonexistent(db_session: AsyncSession) -> None:
    service = _make_service(db_session)
    assert await service.get_by_id(9999) is None


async def test_list_all(db_session: AsyncSession) -> None:
    service = _make_service(db_session)
    await service.create(ArticleCreate(topic="주제 1"))
    await service.create(ArticleCreate(topic="주제 2"))
    await service.create(ArticleCreate(topic="주제 3"))

    articles, total = await service.list_all()
    assert total == 3
    assert len(articles) == 3


async def test_list_pagination(db_session: AsyncSession) -> None:
    service = _make_service(db_session)
    for i in range(5):
        await service.create(ArticleCreate(topic=f"주제 {i}"))

    articles, total = await service.list_all(offset=0, limit=2)
    assert total == 5
    assert len(articles) == 2


async def test_update(db_session: AsyncSession) -> None:
    service = _make_service(db_session)
    created = await service.create(ArticleCreate(topic="원래 주제"))

    updated = await service.update(
        created.id, ArticleUpdate(title="수정됨", category="AI")
    )
    assert updated is not None
    assert updated.title == "수정됨"
    assert updated.category == "AI"


async def test_update_nonexistent(db_session: AsyncSession) -> None:
    service = _make_service(db_session)
    result = await service.update(9999, ArticleUpdate(title="없음"))
    assert result is None


async def test_delete(db_session: AsyncSession) -> None:
    service = _make_service(db_session)
    created = await service.create(ArticleCreate(topic="삭제 대상"))

    assert await service.delete(created.id) is True
    assert await service.get_by_id(created.id) is None


async def test_delete_nonexistent(db_session: AsyncSession) -> None:
    service = _make_service(db_session)
    assert await service.delete(9999) is False

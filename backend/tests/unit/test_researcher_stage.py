from unittest.mock import AsyncMock, MagicMock, patch

from app.pipeline.base import StageInput, StageOutput
from app.pipeline.stages.s2_researcher import ResearcherStage, _deduplicate
from app.pipeline.subagents.base import Reference


def _make_ref(
    url: str = "https://example.com/1",
    title: str = "자료 제목",
    source_type: str = "official",
    relevance_score: float = 0.9,
) -> Reference:
    return Reference(
        url=url,
        title=title,
        summary="요약입니다.",
        source_type=source_type,
        relevance_score=relevance_score,
    )


def _make_input(queries: list[str] | None = None) -> StageInput:
    return StageInput(
        article_id=1,
        slug="ai란-무엇인가",
        topic="AI란 무엇인가?",
        data={"search_queries": queries or ["AI definition", "AI basics"]},
    )


def _make_stage() -> tuple[ResearcherStage, AsyncMock, MagicMock]:
    mock_claude = AsyncMock()
    mock_fm = MagicMock()
    stage = ResearcherStage(mock_claude, mock_fm)
    return stage, mock_claude, mock_fm


async def test_researcher_name() -> None:
    stage, _, _ = _make_stage()
    assert stage.name == "researcher"


async def test_researcher_empty_queries() -> None:
    stage, _, _ = _make_stage()
    stage_input = StageInput(
        article_id=1, slug="test", topic="테스트", data={}
    )

    result = await stage.execute(stage_input)

    assert result.success is False
    assert "search_queries" in result.error


async def test_researcher_empty_queries_list() -> None:
    stage, _, _ = _make_stage()
    stage_input = StageInput(
        article_id=1, slug="test", topic="테스트", data={"search_queries": []}
    )

    result = await stage.execute(stage_input)

    assert result.success is False


async def test_researcher_success_with_all_librarians() -> None:
    stage, _, mock_fm = _make_stage()

    official_refs = [_make_ref("https://official.com/1", "공식1", "official")]
    github_refs = [_make_ref("https://github.com/repo1", "GitHub1", "github")]
    blog_en_refs = [_make_ref("https://blog.com/en1", "EN Blog1", "blog_en")]
    blog_kr_refs = [_make_ref("https://blog.kr/kr1", "KR Blog1", "blog_kr")]

    with patch.object(stage, "_librarians") as mock_libs:
        mock_lib_official = AsyncMock()
        mock_lib_official.search.return_value = official_refs
        mock_lib_github = AsyncMock()
        mock_lib_github.search.return_value = github_refs
        mock_lib_en = AsyncMock()
        mock_lib_en.search.return_value = blog_en_refs
        mock_lib_kr = AsyncMock()
        mock_lib_kr.search.return_value = blog_kr_refs
        mock_libs.__iter__ = lambda self: iter([
            mock_lib_official, mock_lib_github, mock_lib_en, mock_lib_kr
        ])

        result = await stage.execute(_make_input())

    assert result.success is True
    assert result.data["total_count"] == 4
    assert result.data["by_source"]["official"] == 1
    assert result.data["by_source"]["github"] == 1
    assert result.data["by_source"]["blog_en"] == 1
    assert result.data["by_source"]["blog_kr"] == 1
    assert len(result.data["references"]) == 4

    mock_fm.write_json.assert_called_once()
    call_args = mock_fm.write_json.call_args[0]
    assert call_args[0] == "ai란-무엇인가"
    assert call_args[1] == "references.json"


async def test_researcher_handles_librarian_exception() -> None:
    stage, _, mock_fm = _make_stage()

    good_refs = [
        _make_ref("https://official.com/1", "공식1", "official"),
        _make_ref("https://official.com/2", "공식2", "official"),
        _make_ref("https://official.com/3", "공식3", "official"),
    ]

    with patch.object(stage, "_librarians") as mock_libs:
        mock_lib_ok = AsyncMock()
        mock_lib_ok.search.return_value = good_refs
        mock_lib_fail = AsyncMock()
        mock_lib_fail.search.side_effect = RuntimeError("검색 실패")
        mock_lib_empty1 = AsyncMock()
        mock_lib_empty1.search.return_value = []
        mock_lib_empty2 = AsyncMock()
        mock_lib_empty2.search.return_value = []
        mock_libs.__iter__ = lambda self: iter([
            mock_lib_ok, mock_lib_fail, mock_lib_empty1, mock_lib_empty2
        ])

        result = await stage.execute(_make_input())

    assert result.success is True
    assert result.data["total_count"] == 3


async def test_researcher_all_librarians_fail() -> None:
    stage, _, mock_fm = _make_stage()

    with patch.object(stage, "_librarians") as mock_libs:
        mock_lib1 = AsyncMock()
        mock_lib1.search.side_effect = RuntimeError("실패1")
        mock_lib2 = AsyncMock()
        mock_lib2.search.side_effect = RuntimeError("실패2")
        mock_lib3 = AsyncMock()
        mock_lib3.search.side_effect = RuntimeError("실패3")
        mock_lib4 = AsyncMock()
        mock_lib4.search.side_effect = RuntimeError("실패4")
        mock_libs.__iter__ = lambda self: iter([
            mock_lib1, mock_lib2, mock_lib3, mock_lib4
        ])

        result = await stage.execute(_make_input())

    assert result.success is False
    assert "최소 기준" in result.error
    mock_fm.write_json.assert_called_once()


async def test_researcher_deduplicates_by_url() -> None:
    stage, _, _ = _make_stage()

    dup_refs = [
        _make_ref("https://same-url.com", "제목1", "official"),
        _make_ref("https://same-url.com", "제목2", "github"),
        _make_ref("https://unique.com", "제목3", "blog_en"),
        _make_ref("https://unique2.com", "제목4", "blog_kr"),
    ]

    with patch.object(stage, "_librarians") as mock_libs:
        mock_lib = AsyncMock()
        mock_lib.search.return_value = dup_refs
        mock_lib2 = AsyncMock()
        mock_lib2.search.return_value = []
        mock_lib3 = AsyncMock()
        mock_lib3.search.return_value = []
        mock_lib4 = AsyncMock()
        mock_lib4.search.return_value = []
        mock_libs.__iter__ = lambda self: iter([
            mock_lib, mock_lib2, mock_lib3, mock_lib4
        ])

        result = await stage.execute(_make_input())

    assert result.data["total_count"] == 3


async def test_researcher_sorts_by_relevance_desc() -> None:
    stage, _, _ = _make_stage()

    refs = [
        _make_ref("https://a.com", "낮은점수", "official", 0.5),
        _make_ref("https://b.com", "높은점수", "github", 0.99),
        _make_ref("https://c.com", "중간점수", "blog_en", 0.75),
    ]

    with patch.object(stage, "_librarians") as mock_libs:
        mock_lib = AsyncMock()
        mock_lib.search.return_value = refs
        mock_lib2 = AsyncMock()
        mock_lib2.search.return_value = []
        mock_lib3 = AsyncMock()
        mock_lib3.search.return_value = []
        mock_lib4 = AsyncMock()
        mock_lib4.search.return_value = []
        mock_libs.__iter__ = lambda self: iter([
            mock_lib, mock_lib2, mock_lib3, mock_lib4
        ])

        result = await stage.execute(_make_input())

    scores = [r["relevance_score"] for r in result.data["references"]]
    assert scores == sorted(scores, reverse=True)
    assert scores[0] == 0.99


async def test_researcher_saves_references_json() -> None:
    stage, _, mock_fm = _make_stage()

    refs = [_make_ref("https://official.com/1", "자료", "official", 0.9)]

    with patch.object(stage, "_librarians") as mock_libs:
        mock_lib = AsyncMock()
        mock_lib.search.return_value = refs
        mock_lib2 = AsyncMock()
        mock_lib2.search.return_value = []
        mock_lib3 = AsyncMock()
        mock_lib3.search.return_value = []
        mock_lib4 = AsyncMock()
        mock_lib4.search.return_value = []
        mock_libs.__iter__ = lambda self: iter([
            mock_lib, mock_lib2, mock_lib3, mock_lib4
        ])

        await stage.execute(_make_input())

    saved_data = mock_fm.write_json.call_args[0][2]
    assert len(saved_data) == 1
    assert saved_data[0]["url"] == "https://official.com/1"
    assert saved_data[0]["source_type"] == "official"
    assert saved_data[0]["relevance_score"] == 0.9


async def test_researcher_output_structure() -> None:
    stage, _, _ = _make_stage()

    refs = [
        _make_ref("https://a.com", "자료1", "official"),
        _make_ref("https://b.com", "자료2", "official"),
        _make_ref("https://c.com", "자료3", "github"),
    ]

    with patch.object(stage, "_librarians") as mock_libs:
        mock_lib = AsyncMock()
        mock_lib.search.return_value = refs
        mock_lib2 = AsyncMock()
        mock_lib2.search.return_value = []
        mock_lib3 = AsyncMock()
        mock_lib3.search.return_value = []
        mock_lib4 = AsyncMock()
        mock_lib4.search.return_value = []
        mock_libs.__iter__ = lambda self: iter([
            mock_lib, mock_lib2, mock_lib3, mock_lib4
        ])

        result = await stage.execute(_make_input())

    assert isinstance(result, StageOutput)
    assert result.stage_name == "researcher"
    assert "references" in result.data
    assert "total_count" in result.data
    assert "by_source" in result.data


def test_deduplicate_preserves_first_occurrence() -> None:
    refs = [
        _make_ref("https://dup.com", "첫 번째", "official", 0.9),
        _make_ref("https://dup.com", "두 번째", "github", 0.5),
    ]

    unique = _deduplicate(refs)

    assert len(unique) == 1
    assert unique[0].title == "첫 번째"
    assert unique[0].source_type == "official"


def test_deduplicate_empty_list() -> None:
    assert _deduplicate([]) == []


def test_deduplicate_all_unique() -> None:
    refs = [
        _make_ref("https://a.com", "A", "official"),
        _make_ref("https://b.com", "B", "github"),
        _make_ref("https://c.com", "C", "blog_en"),
    ]

    unique = _deduplicate(refs)

    assert len(unique) == 3

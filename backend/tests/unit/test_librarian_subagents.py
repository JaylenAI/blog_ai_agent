from unittest.mock import AsyncMock

from app.pipeline.subagents.base import LibrarianSubagent, Reference
from app.pipeline.subagents.librarian_blog_en import BlogEnLibrarian
from app.pipeline.subagents.librarian_blog_kr import BlogKrLibrarian
from app.pipeline.subagents.librarian_github import GithubLibrarian
from app.pipeline.subagents.librarian_official import OfficialLibrarian

MOCK_REFERENCES = {
    "references": [
        {
            "url": "https://example.com/doc1",
            "title": "공식 문서 1",
            "summary": "핵심 내용 요약입니다.",
            "relevance_score": 0.95,
        },
        {
            "url": "https://example.com/doc2",
            "title": "공식 문서 2",
            "summary": "두 번째 자료 요약.",
            "relevance_score": 0.8,
        },
    ]
}


def _make_claude(
    response: dict | None = None, error: Exception | None = None
) -> AsyncMock:
    mock = AsyncMock()
    if error:
        mock.run_json.side_effect = error
    else:
        mock.run_json.return_value = response or MOCK_REFERENCES
    return mock


async def test_official_librarian_properties() -> None:
    lib = OfficialLibrarian(_make_claude())
    assert lib.name == "librarian-official"
    assert lib.source_type == "official"


async def test_github_librarian_properties() -> None:
    lib = GithubLibrarian(_make_claude())
    assert lib.name == "librarian-github"
    assert lib.source_type == "github"


async def test_blog_en_librarian_properties() -> None:
    lib = BlogEnLibrarian(_make_claude())
    assert lib.name == "librarian-blog-en"
    assert lib.source_type == "blog_en"


async def test_blog_kr_librarian_properties() -> None:
    lib = BlogKrLibrarian(_make_claude())
    assert lib.name == "librarian-blog-kr"
    assert lib.source_type == "blog_kr"


async def test_search_returns_references() -> None:
    mock_claude = _make_claude()
    lib = OfficialLibrarian(mock_claude)

    refs = await lib.search("AI란 무엇인가?", ["AI definition", "AI basics"])

    assert len(refs) == 2
    assert all(isinstance(r, Reference) for r in refs)
    assert refs[0].url == "https://example.com/doc1"
    assert refs[0].title == "공식 문서 1"
    assert refs[0].source_type == "official"
    assert refs[0].relevance_score == 0.95
    mock_claude.run_json.assert_called_once()


async def test_search_sets_source_type_from_librarian() -> None:
    mock_claude = _make_claude()
    lib = GithubLibrarian(mock_claude)

    refs = await lib.search("FastAPI", ["FastAPI github"])

    assert all(r.source_type == "github" for r in refs)


async def test_search_default_relevance_score() -> None:
    response = {
        "references": [
            {
                "url": "https://example.com/no-score",
                "title": "점수 없는 자료",
                "summary": "요약",
            }
        ]
    }
    lib = OfficialLibrarian(_make_claude(response))

    refs = await lib.search("테스트", ["test query"])

    assert refs[0].relevance_score == 0.8


async def test_search_skips_incomplete_references() -> None:
    response = {
        "references": [
            {"url": "https://example.com/valid", "title": "유효", "summary": "요약"},
            {"url": "https://example.com/no-title"},
            {"title": "제목만"},
        ]
    }
    lib = OfficialLibrarian(_make_claude(response))

    refs = await lib.search("테스트", ["query"])

    assert len(refs) == 1
    assert refs[0].url == "https://example.com/valid"


async def test_search_returns_empty_on_runtime_error() -> None:
    lib = OfficialLibrarian(_make_claude(error=RuntimeError("CLI not found")))

    refs = await lib.search("테스트", ["query"])

    assert refs == []


async def test_search_returns_empty_on_value_error() -> None:
    lib = OfficialLibrarian(_make_claude(error=ValueError("No valid JSON")))

    refs = await lib.search("테스트", ["query"])

    assert refs == []


async def test_search_empty_references_array() -> None:
    lib = OfficialLibrarian(_make_claude({"references": []}))

    refs = await lib.search("테스트", ["query"])

    assert refs == []


async def test_search_missing_references_key() -> None:
    lib = OfficialLibrarian(_make_claude({"data": "unexpected"}))

    refs = await lib.search("테스트", ["query"])

    assert refs == []


async def test_reference_is_frozen() -> None:
    ref = Reference(
        url="https://example.com",
        title="제목",
        summary="요약",
        source_type="official",
        relevance_score=0.9,
    )

    try:
        ref.url = "https://changed.com"  # type: ignore[misc]
        raise AssertionError("frozen dataclass에서 mutation이 허용됨")
    except AttributeError:
        pass


async def test_search_prompt_contains_topic_and_queries() -> None:
    mock_claude = _make_claude()
    lib = BlogKrLibrarian(mock_claude)

    await lib.search("Docker 컨테이너", ["docker tutorial", "컨테이너 기초"])

    call_args = mock_claude.run_json.call_args[0][0]
    assert "Docker 컨테이너" in call_args
    assert "docker tutorial" in call_args
    assert "컨테이너 기초" in call_args


async def test_all_librarians_are_subagent_instances() -> None:
    mock_claude = _make_claude()
    librarians = [
        OfficialLibrarian(mock_claude),
        GithubLibrarian(mock_claude),
        BlogEnLibrarian(mock_claude),
        BlogKrLibrarian(mock_claude),
    ]

    for lib in librarians:
        assert isinstance(lib, LibrarianSubagent)

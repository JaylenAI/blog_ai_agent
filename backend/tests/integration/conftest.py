from collections.abc import AsyncGenerator
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.claude.client import ClaudeClient
from app.dependencies import get_db
from app.main import create_app
from app.models.base import Base
from app.utils.file_manager import FileManager

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
SessionFactory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


MOCK_ROUTER_RESPONSE = {
    "slug": "what-is-llm",
    "title": "LLM이란 무엇인가",
    "category": "AI/ML",
    "target_audience": "beginner",
    "search_queries": ["LLM definition", "대규모 언어 모델"],
    "seo_keywords": ["LLM", "대규모 언어 모델", "GPT"],
    "estimated_sections": 8,
}

_MOCK_OFFICIAL_REFS = {
    "references": [
        {"url": "https://arxiv.org/abs/1706.03762", "title": "Attention Is All You Need", "summary": "트랜스포머 아키텍처 원논문", "relevance_score": 0.95},
        {"url": "https://arxiv.org/abs/2005.14165", "title": "GPT-3 논문", "summary": "대규모 언어 모델 스케일링", "relevance_score": 0.92},
        {"url": "https://docs.anthropic.com/overview", "title": "Claude 공식 문서", "summary": "Anthropic Claude 개요", "relevance_score": 0.88},
    ]
}

_MOCK_GITHUB_REFS = {
    "references": [
        {"url": "https://github.com/huggingface/transformers", "title": "Hugging Face Transformers", "summary": "트랜스포머 모델 라이브러리", "relevance_score": 0.90},
        {"url": "https://github.com/openai/gpt-3", "title": "GPT-3 Repository", "summary": "GPT-3 관련 코드", "relevance_score": 0.85},
    ]
}

_MOCK_BLOG_EN_REFS = {
    "references": [
        {"url": "https://blog.example.com/llm-explained", "title": "LLM Explained", "summary": "LLM 기초 설명", "relevance_score": 0.88},
        {"url": "https://blog.example.com/transformer-guide", "title": "Transformer Guide", "summary": "트랜스포머 가이드", "relevance_score": 0.82},
        {"url": "https://blog.example.com/scaling-laws", "title": "Scaling Laws", "summary": "스케일링 법칙 분석", "relevance_score": 0.80},
    ]
}

_MOCK_BLOG_KR_REFS = {
    "references": [
        {"url": "https://d2.naver.com/llm", "title": "네이버 D2 LLM 글", "summary": "LLM 기술 해설", "relevance_score": 0.87},
        {"url": "https://tech.kakao.com/llm-intro", "title": "카카오 LLM 소개", "summary": "LLM 활용 사례", "relevance_score": 0.83},
    ]
}

MOCK_LIBRARIAN_RESPONSES = [_MOCK_OFFICIAL_REFS, _MOCK_GITHUB_REFS, _MOCK_BLOG_EN_REFS, _MOCK_BLOG_KR_REFS]

MOCK_LIBRARIAN_RESPONSE = _MOCK_OFFICIAL_REFS

MOCK_OUTLINE_RESPONSE = {
    "outline": [
        {
            "section_number": 1,
            "heading": "1. 들어가며",
            "key_points": ["LLM 정의"],
            "estimated_words": 500,
        },
        {
            "section_number": 2,
            "heading": "2. LLM의 핵심 개념",
            "key_points": ["트랜스포머"],
            "estimated_words": 800,
        },
        {
            "section_number": 3,
            "heading": "3. 주요 모델 비교",
            "key_points": ["GPT, Claude"],
            "estimated_words": 800,
        },
        {
            "section_number": 4,
            "heading": "4. 학습 과정",
            "key_points": ["사전학습"],
            "estimated_words": 800,
        },
        {
            "section_number": 5,
            "heading": "5. 활용 사례",
            "key_points": ["챗봇"],
            "estimated_words": 800,
        },
        {
            "section_number": 6,
            "heading": "6. 한계와 과제",
            "key_points": ["환각"],
            "estimated_words": 800,
        },
        {
            "section_number": 7,
            "heading": "7. 미래 전망",
            "key_points": ["AGI"],
            "estimated_words": 600,
        },
        {
            "section_number": 8,
            "heading": "8. 마치며",
            "key_points": ["정리"],
            "estimated_words": 400,
        },
    ],
    "total_sections": 8,
    "estimated_total_words": 5500,
    "approach": "설명형",
}

_SECTION_BODY = "가" * 800

MOCK_FULL_CONTENT = (
    "# LLM이란 무엇인가\n\n"
    + "## 1. 들어가며\n\n" + "가" * 500 + "\n\n"
    + "## 2. LLM의 핵심 개념\n\n" + _SECTION_BODY + "\n\n"
    + "## 3. 주요 모델 비교\n\n" + _SECTION_BODY + "\n\n"
    + "## 4. 학습 과정\n\n" + _SECTION_BODY + "\n\n"
    + "## 5. 활용 사례\n\n" + _SECTION_BODY + "\n\n"
    + "## 6. 한계와 과제\n\n" + _SECTION_BODY + "\n\n"
    + "## 7. 미래 전망\n\n" + "가" * 600 + "\n\n"
    + "## 8. 마치며\n\n" + "가" * 400
)

MOCK_CRITIQUE = {
    "validations": [
        {
            "category": "style",
            "item": "격식체 사용",
            "passed": True,
            "score": 0.95,
            "message": "격식체 확인됨",
        },
        {
            "category": "style",
            "item": "구조 일관성",
            "passed": True,
            "score": 0.90,
            "message": "구조 양호",
        },
        {
            "category": "seo",
            "item": "키워드 밀도",
            "passed": True,
            "score": 0.88,
            "message": "적정 키워드 밀도",
        },
        {
            "category": "seo",
            "item": "메타 디스크립션",
            "passed": True,
            "score": 0.85,
            "message": "메타 양호",
        },
        {
            "category": "aeo",
            "item": "직접 답변 구조",
            "passed": True,
            "score": 0.80,
            "message": "답변 구조 확인",
        },
        {
            "category": "geo",
            "item": "E-E-A-T 시그널",
            "passed": False,
            "score": 0.65,
            "message": "인용 부족",
        },
    ]
}

MOCK_VALIDATOR_RESPONSE = {
    "validations": MOCK_CRITIQUE["validations"],
}


@dataclass(frozen=True)
class MockClaudeResponse:
    text: str
    session_id: str = ""
    cost_usd: float = 0.0


@pytest.fixture(autouse=True)
async def setup_db() -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionFactory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def tmp_file_manager(tmp_path: Path) -> FileManager:
    return FileManager(base_dir=tmp_path)


MOCK_IMAGE_PLAN = {"images": []}

def build_mock_claude(*, full_pipeline: bool = False) -> AsyncMock:
    mock = AsyncMock(spec=ClaudeClient)
    if full_pipeline:
        mock.run_json.side_effect = [
            MOCK_ROUTER_RESPONSE,
            *MOCK_LIBRARIAN_RESPONSES,
            MOCK_OUTLINE_RESPONSE,
            MOCK_IMAGE_PLAN,
            MOCK_VALIDATOR_RESPONSE,
        ]
        mock.run.return_value = MockClaudeResponse(
            text=MOCK_FULL_CONTENT
        )
    else:
        mock.run_json.side_effect = [
            MOCK_ROUTER_RESPONSE,
            *MOCK_LIBRARIAN_RESPONSES,
            MOCK_OUTLINE_RESPONSE,
            MOCK_VALIDATOR_RESPONSE,
        ]
    return mock


def build_mock_file_manager(
    *, with_content: bool = False
) -> MagicMock:
    mock = MagicMock(spec=FileManager)
    if with_content:
        def read_json_effect(
            slug: str, filename: str
        ) -> dict | list | None:
            if filename == "meta.json":
                return MOCK_ROUTER_RESPONSE
            if filename == "outline.json":
                return MOCK_OUTLINE_RESPONSE
            if filename == "references.json":
                return MOCK_LIBRARIAN_RESPONSE["references"]
            if filename == "critique.json":
                return MOCK_CRITIQUE
            return None

        def read_text_effect(
            slug: str, filename: str
        ) -> str | None:
            if filename == "final.md":
                return MOCK_FULL_CONTENT
            return None

        mock.read_json.side_effect = read_json_effect
        mock.read_text.side_effect = read_text_effect
    else:
        mock.read_json.return_value = None
        mock.read_text.return_value = None
    return mock


@pytest.fixture
async def integration_client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as ac:
        yield ac

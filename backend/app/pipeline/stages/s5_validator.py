import re

from app.claude.client import ClaudeClient
from app.claude.prompts.validator import ValidatorPrompt
from app.pipeline.base import Stage, StageInput, StageOutput
from app.utils.file_manager import FileManager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ValidatorStage(Stage):
    def __init__(self, claude: ClaudeClient, file_manager: FileManager) -> None:
        self._claude = claude
        self._fm = file_manager
        self._prompt = ValidatorPrompt()

    @property
    def name(self) -> str:
        return "validator"

    async def execute(self, stage_input: StageInput) -> StageOutput:
        content = self._fm.read_text(stage_input.slug, "final.md")
        if not content:
            return StageOutput(
                stage_name=self.name,
                success=False,
                error="final.md를 찾을 수 없습니다",
            )

        meta = self._fm.read_json(stage_input.slug, "meta.json") or {}

        rule_results = _run_rule_checks(content, meta)

        try:
            seo_keywords = ", ".join(meta.get("seo_keywords", []))
            result = await self._claude.run_json(
                self._prompt.render(
                    content=content,
                    seo_keywords=seo_keywords or "키워드 없음",
                )
            )
            claude_results = result.get("validations", [])
        except (RuntimeError, ValueError) as e:
            logger.warning("Validator Claude 평가 실패: %s", e)
            claude_results = []

        all_validations = rule_results + claude_results

        critique = {
            "validations": all_validations,
            "summary": _compute_summary(all_validations),
        }
        self._fm.write_json(stage_input.slug, "critique.json", critique)

        logger.info(
            "Validator 완료: %d/%d 통과 (%.0f%%)",
            critique["summary"]["passed"],
            critique["summary"]["total"],
            critique["summary"]["score"] * 100,
        )

        return StageOutput(
            stage_name=self.name,
            success=True,
            data=critique,
        )


def _run_rule_checks(content: str, meta: dict) -> list[dict]:
    return [
        _check_char_count(content),
        _check_section_count(content),
        _check_intro_section(content),
        _check_conclusion_section(content),
        _check_no_faq(content),
        _check_no_references_section(content),
        _check_html_tables(content),
        _check_title_length(meta),
        _check_keyword_presence(content, meta),
    ]


def _check_char_count(content: str) -> dict:
    count = len(content)
    passed = 6000 <= count <= 13000
    return {
        "category": "style",
        "item": "분량 검증 (6,000~13,000자)",
        "passed": passed,
        "score": 1.0 if passed else 0.0,
        "message": f"{count:,}자" + ("" if passed else " — 범위 초과"),
    }


def _check_section_count(content: str) -> dict:
    count = content.count("## ")
    passed = 7 <= count <= 12
    return {
        "category": "style",
        "item": "섹션 수 검증 (7~12개)",
        "passed": passed,
        "score": 1.0 if passed else 0.0,
        "message": f"{count}개 섹션" + ("" if passed else " — 범위 초과"),
    }


def _check_intro_section(content: str) -> dict:
    passed = "들어가며" in content
    return {
        "category": "style",
        "item": "들어가며 섹션 존재",
        "passed": passed,
        "score": 1.0 if passed else 0.0,
        "message": "확인됨" if passed else "들어가며 섹션 없음",
    }


def _check_conclusion_section(content: str) -> dict:
    passed = "마치며" in content
    return {
        "category": "style",
        "item": "마치며 섹션 존재",
        "passed": passed,
        "score": 1.0 if passed else 0.0,
        "message": "확인됨" if passed else "마치며 섹션 없음",
    }


def _check_no_faq(content: str) -> dict:
    upper = content.upper()
    has_faq = "FAQ" in upper or "자주 묻는" in content
    return {
        "category": "style",
        "item": "FAQ 섹션 미포함",
        "passed": not has_faq,
        "score": 1.0 if not has_faq else 0.0,
        "message": "통과" if not has_faq else "FAQ 섹션 감지됨",
    }


def _check_no_references_section(content: str) -> dict:
    markers = ["## 참고 자료", "## 참고자료", "## References"]
    has_refs = any(m in content for m in markers)
    return {
        "category": "style",
        "item": "참고 자료 목록 섹션 미포함",
        "passed": not has_refs,
        "score": 1.0 if not has_refs else 0.0,
        "message": "통과" if not has_refs else "참고 자료 목록 섹션 감지됨",
    }


def _check_html_tables(content: str) -> dict:
    no_code = re.sub(r"```[\s\S]*?```", "", content)
    has_pipe_table = "|---" in no_code or "| ---" in no_code
    if has_pipe_table:
        return {
            "category": "style",
            "item": "HTML 표 사용",
            "passed": False,
            "score": 0.0,
            "message": "마크다운 파이프 표 감지됨 — HTML <table> 사용 필요",
        }
    return {
        "category": "style",
        "item": "HTML 표 사용",
        "passed": True,
        "score": 1.0,
        "message": "통과",
    }


def _check_title_length(meta: dict) -> dict:
    title = meta.get("title", "")
    length = len(title)
    passed = 0 < length <= 60
    return {
        "category": "seo",
        "item": "제목 길이 (60자 이내)",
        "passed": passed,
        "score": 1.0 if passed else 0.0,
        "message": f"{length}자" + ("" if passed else " — 60자 초과"),
    }


def _check_keyword_presence(content: str, meta: dict) -> dict:
    keywords = meta.get("seo_keywords", [])
    if not keywords:
        return {
            "category": "seo",
            "item": "키워드 본문 출현",
            "passed": False,
            "score": 0.0,
            "message": "키워드 정보 없음",
        }

    found = sum(1 for kw in keywords if kw.lower() in content.lower())
    ratio = found / len(keywords)
    passed = ratio >= 0.5
    return {
        "category": "seo",
        "item": "키워드 본문 출현",
        "passed": passed,
        "score": round(ratio, 2),
        "message": f"{found}/{len(keywords)} 키워드 출현",
    }


def _compute_summary(validations: list[dict]) -> dict:
    total = len(validations)
    passed = sum(1 for v in validations if v.get("passed"))

    by_category: dict[str, dict[str, int]] = {}
    for v in validations:
        cat = v.get("category", "unknown")
        if cat not in by_category:
            by_category[cat] = {"total": 0, "passed": 0}
        by_category[cat]["total"] += 1
        if v.get("passed"):
            by_category[cat]["passed"] += 1

    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "score": round(passed / total, 2) if total > 0 else 0.0,
        "by_category": by_category,
    }

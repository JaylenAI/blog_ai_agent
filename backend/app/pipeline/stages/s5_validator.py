import re
import statistics

from app.claude.client import ClaudeClient
from app.claude.prompts.oracle import OraclePrompt
from app.claude.prompts.validator import ValidatorPrompt
from app.config import settings
from app.formats import get_format_registry
from app.formats.schema import FormatSpec
from app.pipeline.base import Stage, StageInput, StageOutput
from app.utils.file_manager import FileManager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ValidatorStage(Stage):
    def __init__(self, claude: ClaudeClient, file_manager: FileManager) -> None:
        self._claude = claude
        self._fm = file_manager
        self._prompt = ValidatorPrompt()
        self._oracle_prompt = OraclePrompt()

    @property
    def name(self) -> str:
        return "validator"

    async def execute(
        self,
        stage_input: StageInput,
        on_progress: "ProgressCallback | None" = None,
    ) -> StageOutput:
        content = self._fm.read_text(stage_input.slug, "final.md")
        if not content:
            return StageOutput(
                stage_name=self.name,
                success=False,
                error="final.md를 찾을 수 없습니다",
            )

        meta = self._fm.read_json(stage_input.slug, "meta.json") or {}

        format_id = meta.get("format_id", stage_input.format_id)
        registry = get_format_registry()
        format_spec = registry.get(format_id)

        rule_results = _run_rule_checks(content, meta, format_spec)

        try:
            seo_keywords = ", ".join(meta.get("seo_keywords", []))
            result = await self._claude.run_json(
                self._prompt.render(
                    content=content,
                    seo_keywords=seo_keywords or "키워드 없음",
                    format_spec=format_spec,
                )
            )
            claude_results = result.get("validations", [])
        except (RuntimeError, ValueError) as e:
            logger.warning("Validator Claude 평가 실패: %s", e)
            claude_results = []

        all_validations = rule_results + claude_results

        use_oracle = (
            stage_input.data.get("use_oracle", False)
            or len(content) >= settings.oracle_threshold_chars
        )
        oracle_results: list[dict] = []
        if use_oracle:
            oracle_results = await self._run_oracle(content, meta)
            all_validations = all_validations + oracle_results

        critique = {
            "validations": all_validations,
            "summary": _compute_summary(all_validations),
            "oracle_used": use_oracle,
        }
        self._fm.write_json(stage_input.slug, "critique.json", critique)

        logger.info(
            "Validator 완료: %d/%d 통과 (%.0f%%), format=%s, oracle=%s",
            critique["summary"]["passed"],
            critique["summary"]["total"],
            critique["summary"]["score"] * 100,
            format_id,
            use_oracle,
        )

        return StageOutput(
            stage_name=self.name,
            success=True,
            data=critique,
        )

    async def _run_oracle(self, content: str, meta: dict) -> list[dict]:
        try:
            seo_keywords = ", ".join(meta.get("seo_keywords", []))
            result = await self._claude.run_json(
                self._oracle_prompt.render(
                    content=content,
                    seo_keywords=seo_keywords or "키워드 없음",
                )
            )
            oracle_items = result.get("validations", [])
            for item in oracle_items:
                item["item"] = f"[Oracle] {item.get('item', '')}"
            logger.info("Oracle 검증 완료: %d 항목", len(oracle_items))
            return oracle_items
        except (RuntimeError, ValueError) as e:
            logger.warning("Oracle 검증 실패: %s", e)
            return []


def _run_rule_checks(
    content: str, meta: dict, format_spec: FormatSpec
) -> list[dict]:
    return [
        _check_char_count(content, format_spec),
        _check_section_count(content, format_spec),
        _check_intro_section(content, format_spec),
        _check_conclusion_section(content, format_spec),
        _check_no_faq(content),
        _check_no_references_section(content),
        _check_html_tables(content),
        _check_title_length(meta),
        _check_keyword_presence(content, meta),
        _check_slop_can_do(content),
        _check_slop_empty_emphasis(content),
        _check_slop_monotony(content),
        _check_slop_superlatives(content),
        _check_readability(content),
        _check_keyword_density(content, meta),
        _check_heading_keyword(content, meta),
        _check_image_alt(content),
        _check_definition_patterns(content),
        _check_comparison_tables(content),
        _check_quantitative_data(content),
        _check_ai_tell_words(content),
        _check_burstiness(content),
    ]


def _check_char_count(content: str, spec: FormatSpec) -> dict:
    count = len(content)
    min_chars = spec.structure.char_count.standard[0]
    max_chars = spec.structure.char_count.long[1]
    passed = min_chars <= count <= max_chars
    return {
        "category": "style",
        "item": f"분량 검증 ({min_chars:,}~{max_chars:,}자)",
        "passed": passed,
        "score": 1.0 if passed else 0.0,
        "message": f"{count:,}자" + ("" if passed else " — 범위 초과"),
    }


def _check_section_count(content: str, spec: FormatSpec) -> dict:
    count = content.count("## ")
    sc = spec.structure.section_count
    passed = sc.min <= count <= sc.max + 3
    return {
        "category": "style",
        "item": f"섹션 수 검증 ({sc.min}~{sc.max + 3}개)",
        "passed": passed,
        "score": 1.0 if passed else 0.0,
        "message": f"{count}개 섹션" + ("" if passed else " — 범위 초과"),
    }


def _check_intro_section(content: str, spec: FormatSpec) -> dict:
    keywords = spec.validation.intro_keywords
    found = any(kw in content for kw in keywords)
    return {
        "category": "style",
        "item": f"도입 섹션 존재 ({', '.join(keywords)})",
        "passed": found,
        "score": 1.0 if found else 0.0,
        "message": "확인됨" if found else "도입 섹션 없음",
    }


def _check_conclusion_section(content: str, spec: FormatSpec) -> dict:
    keywords = spec.validation.closing_keywords
    found = any(kw in content for kw in keywords)
    return {
        "category": "style",
        "item": f"마무리 섹션 존재 ({', '.join(keywords)})",
        "passed": found,
        "score": 1.0 if found else 0.0,
        "message": "확인됨" if found else "마무리 섹션 없음",
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


def _check_slop_can_do(content: str) -> dict:
    count = len(re.findall(r"할 수 있습니다", content))
    threshold = settings.slop_can_do_threshold
    passed = count <= threshold
    score = max(0.0, 1.0 - (count - threshold) * 0.15) if not passed else 1.0
    return {
        "category": "style",
        "item": "AI 슬롭: '~할 수 있습니다' 반복",
        "passed": passed,
        "score": round(score, 2),
        "message": f"{count}회 출현" + ("" if passed else f" — {threshold}회 이하 권장"),
    }


def _check_slop_empty_emphasis(content: str) -> dict:
    patterns = [
        r"매우 중요",
        r"핵심적입니다",
        r"가장 중요한",
        r"굉장히 중요",
        r"매우 핵심",
        r"반드시 알아야",
    ]
    hits = sum(len(re.findall(p, content)) for p in patterns)
    threshold = settings.slop_emphasis_threshold
    passed = hits <= threshold
    score = max(0.0, 1.0 - (hits - threshold) * 0.2) if not passed else 1.0
    return {
        "category": "style",
        "item": "AI 슬롭: 빈 강조 표현",
        "passed": passed,
        "score": round(score, 2),
        "message": f"{hits}회 감지" + ("" if passed else f" — {threshold}회 이하 권장"),
    }


def _check_slop_monotony(content: str) -> dict:
    sentences = re.split(r"[.?!]\s", content)
    endings = [s.strip()[-3:] for s in sentences if len(s.strip()) > 3]
    max_streak = 1
    streak = 1
    for i in range(1, len(endings)):
        if endings[i] == endings[i - 1]:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 1
    passed = max_streak < 4
    return {
        "category": "style",
        "item": "AI 슬롭: 문장 구조 반복",
        "passed": passed,
        "score": 1.0 if passed else max(0.0, 1.0 - (max_streak - 3) * 0.25),
        "message": f"최대 연속 동일 어미 {max_streak}회" + ("" if passed else " — 다양한 어미 사용 권장"),
    }


def _check_slop_superlatives(content: str) -> dict:
    patterns = [
        r"최고의\s",
        r"유일한\s",
        r"가장 좋은\s",
        r"가장 뛰어난\s",
        r"완벽한\s",
        r"없어서는 안 될\s",
    ]
    hits = sum(len(re.findall(p, content)) for p in patterns)
    threshold = settings.slop_superlatives_threshold
    passed = hits <= threshold
    return {
        "category": "style",
        "item": "AI 슬롭: 근거 없는 단정",
        "passed": passed,
        "score": 1.0 if passed else max(0.0, 1.0 - (hits - threshold) * 0.25),
        "message": f"{hits}회 감지" + ("" if passed else " — 근거 제시 필요"),
    }


def _check_readability(content: str) -> dict:
    plain = re.sub(r"```[\s\S]*?```", "", content)
    plain = re.sub(r"<[^>]+>", "", plain)
    plain = re.sub(r"[#*\->`|]", "", plain)
    sentences = [s.strip() for s in re.split(r"[.?!]\s", plain) if len(s.strip()) > 5]
    if not sentences:
        return {
            "category": "style",
            "item": "가독성 점수",
            "passed": False,
            "score": 0.0,
            "message": "문장을 감지할 수 없습니다",
        }
    avg_len = sum(len(s) for s in sentences) / len(sentences)
    passed = settings.sentence_length_min <= avg_len <= settings.sentence_length_max
    if avg_len < settings.sentence_length_min:
        score = avg_len / settings.sentence_length_min
        msg = f"평균 문장 길이 {avg_len:.0f}자 — 너무 짧음"
    elif avg_len > settings.sentence_length_max:
        score = max(0.0, 1.0 - (avg_len - settings.sentence_length_max) / 40)
        msg = f"평균 문장 길이 {avg_len:.0f}자 — 너무 김"
    else:
        score = 1.0
        msg = f"평균 문장 길이 {avg_len:.0f}자"
    return {
        "category": "style",
        "item": "가독성 점수",
        "passed": passed,
        "score": round(score, 2),
        "message": msg,
    }


def _check_keyword_density(content: str, meta: dict) -> dict:
    keywords = meta.get("seo_keywords", [])
    if not keywords:
        return {
            "category": "seo",
            "item": "키워드 밀도 (0.5~2.5%)",
            "passed": False,
            "score": 0.0,
            "message": "키워드 정보 없음",
        }
    primary = keywords[0].lower()
    total_chars = len(content)
    if total_chars == 0:
        return {
            "category": "seo",
            "item": "키워드 밀도 (0.5~2.5%)",
            "passed": False,
            "score": 0.0,
            "message": "본문 없음",
        }
    count = content.lower().count(primary)
    density = (count * len(primary)) / total_chars
    passed = settings.keyword_density_min <= density <= settings.keyword_density_max
    return {
        "category": "seo",
        "item": "키워드 밀도 (0.5~2.5%)",
        "passed": passed,
        "score": 1.0 if passed else max(0.0, 1.0 - abs(density - 0.015) * 50),
        "message": f"'{primary}' 밀도 {density * 100:.2f}%"
        + ("" if passed else " — 0.5~2.5% 권장"),
    }


def _check_heading_keyword(content: str, meta: dict) -> dict:
    keywords = meta.get("seo_keywords", [])
    if not keywords:
        return {
            "category": "seo",
            "item": "H2/H3 키워드 포함",
            "passed": False,
            "score": 0.0,
            "message": "키워드 정보 없음",
        }
    headings = re.findall(r"^#{2,3}\s+(.+)$", content, re.MULTILINE)
    if not headings:
        return {
            "category": "seo",
            "item": "H2/H3 키워드 포함",
            "passed": False,
            "score": 0.0,
            "message": "H2/H3 헤딩 없음",
        }
    kw_lower = [kw.lower() for kw in keywords]
    matched = sum(
        1 for h in headings if any(kw in h.lower() for kw in kw_lower)
    )
    ratio = matched / len(headings)
    passed = ratio >= 0.3
    return {
        "category": "seo",
        "item": "H2/H3 키워드 포함",
        "passed": passed,
        "score": round(min(1.0, ratio / 0.3), 2),
        "message": f"{matched}/{len(headings)} 헤딩에 키워드 포함"
        + ("" if passed else " — 30% 이상 권장"),
    }


def _check_image_alt(content: str) -> dict:
    images = re.findall(r"!\[([^\]]*)\]\(", content)
    if not images:
        return {
            "category": "seo",
            "item": "이미지 alt 텍스트",
            "passed": True,
            "score": 1.0,
            "message": "이미지 없음 (해당 없음)",
        }
    empty_alt = sum(1 for alt in images if not alt.strip())
    passed = empty_alt == 0
    return {
        "category": "seo",
        "item": "이미지 alt 텍스트",
        "passed": passed,
        "score": 1.0 if passed else round(1.0 - empty_alt / len(images), 2),
        "message": f"{len(images)}개 이미지 중 {empty_alt}개 alt 누락"
        if not passed
        else f"{len(images)}개 이미지 모두 alt 있음",
    }


def _check_definition_patterns(content: str) -> dict:
    patterns = [
        r"(?:이란|란|은|는)\s*[^.]*(?:을 의미|를 의미|을 뜻|를 뜻|이다|입니다)",
        r"(?:정의|개념|의미)(?:는|란|에 대해)",
        r"즉,?\s+",
    ]
    hits = sum(len(re.findall(p, content)) for p in patterns)
    passed = hits >= 2
    return {
        "category": "aeo",
        "item": "정의 패턴 (AEO)",
        "passed": passed,
        "score": min(1.0, hits / 2),
        "message": f"{hits}개 정의 패턴 감지"
        + ("" if passed else " — 2개 이상 권장 (AI 답변 추출에 유리)"),
    }


def _check_comparison_tables(content: str) -> dict:
    has_table = "<table" in content.lower()
    comparison_hints = len(re.findall(
        r"(?:비교|차이점|장단점|vs\.?|versus|대비)", content, re.IGNORECASE
    ))
    if comparison_hints >= 2 and not has_table:
        return {
            "category": "aeo",
            "item": "비교 테이블 (AEO)",
            "passed": False,
            "score": 0.3,
            "message": f"비교 키워드 {comparison_hints}회 감지 — 비교표 추가 권장",
        }
    return {
        "category": "aeo",
        "item": "비교 테이블 (AEO)",
        "passed": True,
        "score": 1.0,
        "message": "통과" + (f" (비교 키워드 {comparison_hints}회)" if comparison_hints else ""),
    }


def _check_quantitative_data(content: str) -> dict:
    number_patterns = re.findall(
        r"\d+(?:\.\d+)?(?:%|퍼센트|배|억|만|천|GB|MB|ms|초|분|시간)", content
    )
    passed = len(number_patterns) >= 3
    return {
        "category": "geo",
        "item": "정량적 데이터 (GEO)",
        "passed": passed,
        "score": min(1.0, len(number_patterns) / 3),
        "message": f"{len(number_patterns)}개 수치 데이터 감지"
        + ("" if passed else " — 3개 이상 권장 (AI 인용에 유리)"),
    }


def _check_ai_tell_words(content: str) -> dict:
    tell_words = [
        r"살펴보겠습니다",
        r"알아보겠습니다",
        r"알아보도록 하겠습니다",
        r"확인해 보겠습니다",
        r"다루어 보겠습니다",
        r"이해하는 것이 중요합니다",
        r"주목할 만합니다",
        r"주목할 필요가 있습니다",
        r"과언이 아닙니다",
    ]
    hits = sum(len(re.findall(p, content)) for p in tell_words)
    threshold = 4
    passed = hits <= threshold
    score = max(0.0, 1.0 - (hits - threshold) * 0.15) if not passed else 1.0
    return {
        "category": "style",
        "item": "AI Tell-word 감지",
        "passed": passed,
        "score": round(score, 2),
        "message": f"{hits}회 감지"
        + ("" if passed else f" — {threshold}회 이하 권장"),
    }


def _check_burstiness(content: str) -> dict:
    plain = re.sub(r"```[\s\S]*?```", "", content)
    plain = re.sub(r"<[^>]+>", "", plain)
    plain = re.sub(r"[#*\->`|]", "", plain)
    sentences = [s.strip() for s in re.split(r"[.?!]\s", plain) if len(s.strip()) > 3]
    if len(sentences) < 5:
        return {
            "category": "geo",
            "item": "Burstiness 점수",
            "passed": True,
            "score": 1.0,
            "message": "문장 수 부족 (해당 없음)",
        }
    lengths = [len(s) for s in sentences]
    std = statistics.stdev(lengths)
    passed = std >= settings.burstiness_min_std
    return {
        "category": "geo",
        "item": "Burstiness 점수",
        "passed": passed,
        "score": min(1.0, std / settings.burstiness_min_std) if not passed else 1.0,
        "message": f"문장 길이 표준편차 {std:.1f}"
        + ("" if passed else f" — {settings.burstiness_min_std} 이상 권장 (자연스러운 글)"),
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

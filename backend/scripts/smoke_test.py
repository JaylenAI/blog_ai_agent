"""파이프라인 스모크 테스트 — 실제 Claude CLI 호출로 각 Stage 검증.

사용법:
    uv run python scripts/smoke_test.py                    # 전체 파이프라인
    uv run python scripts/smoke_test.py --stage router     # Router만
    uv run python scripts/smoke_test.py --stage researcher # Researcher만
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.claude.client import ClaudeClient
from app.pipeline.base import StageInput
from app.pipeline.stages.s1_router import RouterStage
from app.pipeline.stages.s2_researcher import ResearcherStage
from app.pipeline.stages.s3_outliner import OutlinerStage
from app.pipeline.stages.s4_generator import GeneratorStage
from app.pipeline.stages.s5_validator import ValidatorStage
from app.utils.file_manager import FileManager

TOPIC = "LLM이란 무엇인가"
SLUG = "smoke-test-llm"
BASE_DIR = Path("/tmp/sisyphus_smoke")


def _print_header(stage_name: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  Stage: {stage_name}")
    print(f"{'=' * 60}")


def _print_result(
    stage_name: str, success: bool, elapsed: float, data: dict
) -> None:
    status = "성공" if success else "실패"
    print(f"\n  [{status}] {stage_name} ({elapsed:.1f}초)")
    if data:
        print(f"  데이터 키: {list(data.keys())}")


async def run_router(
    claude: ClaudeClient, fm: FileManager
) -> dict:
    _print_header("Router")
    stage = RouterStage(claude, fm)
    stage_input = StageInput(
        article_id=1, slug=SLUG, topic=TOPIC
    )

    start = time.time()
    output = await stage.execute(stage_input)
    elapsed = time.time() - start

    _print_result("Router", output.success, elapsed, output.data)

    if output.success:
        print(f"  slug: {output.data.get('slug')}")
        print(f"  title: {output.data.get('title')}")
        print(f"  keywords: {output.data.get('seo_keywords', [])[:5]}")

    if not output.success:
        print(f"  에러: {output.error}")

    return output.data


async def run_researcher(
    claude: ClaudeClient, fm: FileManager, router_data: dict
) -> dict:
    _print_header("Researcher (4 Librarian 병렬)")
    stage = ResearcherStage(claude, fm)
    stage_input = StageInput(
        article_id=1, slug=SLUG, topic=TOPIC, data=router_data
    )

    start = time.time()
    output = await stage.execute(stage_input)
    elapsed = time.time() - start

    _print_result(
        "Researcher", output.success, elapsed, output.data
    )

    if output.success:
        total = output.data.get("total_count", 0)
        by_source = output.data.get("by_source", {})
        print(f"  총 참고자료: {total}건")
        for src, cnt in by_source.items():
            print(f"    {src}: {cnt}건")

    if not output.success:
        print(f"  에러: {output.error}")

    return output.data


async def run_outliner(
    claude: ClaudeClient, fm: FileManager, researcher_data: dict
) -> dict:
    _print_header("Outliner")
    stage = OutlinerStage(claude, fm)
    stage_input = StageInput(
        article_id=1, slug=SLUG, topic=TOPIC, data=researcher_data
    )

    start = time.time()
    output = await stage.execute(stage_input)
    elapsed = time.time() - start

    _print_result("Outliner", output.success, elapsed, output.data)

    if output.success:
        outline = output.data.get("outline", [])
        print(f"  섹션 수: {len(outline)}")
        for sec in outline[:3]:
            print(f"    - {sec.get('heading', 'N/A')}")
        if len(outline) > 3:
            print(f"    ... 외 {len(outline) - 3}개")

    if not output.success:
        print(f"  에러: {output.error}")

    return output.data


async def run_generator(
    claude: ClaudeClient, fm: FileManager, outliner_data: dict
) -> dict:
    _print_header("Generator")
    stage = GeneratorStage(claude, fm)
    stage_input = StageInput(
        article_id=1, slug=SLUG, topic=TOPIC, data=outliner_data
    )

    start = time.time()
    output = await stage.execute(stage_input)
    elapsed = time.time() - start

    _print_result("Generator", output.success, elapsed, output.data)

    final_path = BASE_DIR / SLUG / "final.md"
    if final_path.exists():
        content = final_path.read_text()
        print(f"  final.md: {len(content)}자")
        print(
            f"  첫 100자: {content[:100].replace(chr(10), ' ')}..."
        )

    if not output.success:
        print(f"  에러: {output.error}")

    return output.data


async def run_validator(
    claude: ClaudeClient, fm: FileManager, generator_data: dict
) -> dict:
    _print_header("Validator")
    stage = ValidatorStage(claude, fm)
    stage_input = StageInput(
        article_id=1, slug=SLUG, topic=TOPIC, data=generator_data
    )

    start = time.time()
    output = await stage.execute(stage_input)
    elapsed = time.time() - start

    _print_result("Validator", output.success, elapsed, output.data)

    critique_path = BASE_DIR / SLUG / "critique.json"
    if critique_path.exists():
        critique = json.loads(critique_path.read_text())
        validations = critique.get("validations", [])
        passed = sum(1 for v in validations if v.get("passed"))
        print(f"  검증 항목: {len(validations)}개")
        print(f"  통과: {passed}/{len(validations)}")

    if not output.success:
        print(f"  에러: {output.error}")

    return output.data


STAGES = {
    "router": run_router,
    "researcher": run_researcher,
    "outliner": run_outliner,
    "generator": run_generator,
    "validator": run_validator,
}


async def main(target_stage: str | None = None) -> None:
    claude = ClaudeClient()
    fm = FileManager(base_dir=BASE_DIR)

    print(f"주제: {TOPIC}")
    print(f"작업 디렉토리: {BASE_DIR / SLUG}")

    if target_stage:
        if target_stage not in STAGES:
            print(f"알 수 없는 스테이지: {target_stage}")
            print(f"사용 가능: {list(STAGES.keys())}")
            return

        print(f"\n단일 스테이지 실행: {target_stage}")
        if target_stage == "router":
            await run_router(claude, fm)
        else:
            meta = fm.read_json(SLUG, "meta.json")
            if not meta:
                print("meta.json 없음 — router부터 실행해주세요")
                return
            if target_stage == "researcher":
                await run_researcher(claude, fm, dict(meta))
            elif target_stage == "outliner":
                refs = fm.read_json(SLUG, "references.json")
                await run_outliner(
                    claude, fm, {"references": refs or []}
                )
            elif target_stage == "generator":
                outline = fm.read_json(SLUG, "outline.json")
                await run_generator(
                    claude, fm, {"outline": outline or {}}
                )
            elif target_stage == "validator":
                await run_validator(claude, fm, {})
        return

    print("\n전체 파이프라인 실행 (Gate 제외)")
    total_start = time.time()

    router_data = await run_router(claude, fm)
    if not router_data:
        print("\nRouter 실패 — 중단")
        return

    researcher_data = await run_researcher(claude, fm, router_data)
    if not researcher_data:
        print("\nResearcher 실패 — 중단")
        return

    outliner_data = await run_outliner(
        claude, fm, researcher_data
    )
    if not outliner_data:
        print("\nOutliner 실패 — 중단")
        return

    generator_data = await run_generator(
        claude, fm, outliner_data
    )
    if not generator_data:
        print("\nGenerator 실패 — 중단")
        return

    await run_validator(claude, fm, generator_data)

    total_elapsed = time.time() - total_start
    print(f"\n{'=' * 60}")
    print(f"  전체 소요시간: {total_elapsed:.1f}초 ({total_elapsed/60:.1f}분)")
    print(f"{'=' * 60}")

    files = fm.list_files(SLUG)
    print(f"\n  생성된 파일 ({len(files)}개):")
    for f in files:
        print(f"    - {f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="파이프라인 스모크 테스트"
    )
    parser.add_argument(
        "--stage",
        choices=list(STAGES.keys()),
        help="특정 스테이지만 실행",
    )
    args = parser.parse_args()
    asyncio.run(main(args.stage))

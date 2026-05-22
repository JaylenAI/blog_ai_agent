import asyncio
import shutil
from datetime import UTC, datetime

from fastapi import APIRouter

from app.config import settings
from app.schemas.common import ApiResponse

router = APIRouter()


@router.get("/health")
async def health_check() -> ApiResponse[dict]:
    return ApiResponse(
        success=True,
        data={
            "status": "healthy",
            "timestamp": datetime.now(UTC).isoformat(),
            "version": "0.1.0",
        },
    )


@router.get("/health/detailed")
async def health_detailed() -> ApiResponse[dict]:
    checks: dict[str, dict] = {}

    try:
        from sqlalchemy import text

        from app.db.session import async_session_factory
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok"}
    except Exception as e:
        checks["database"] = {"status": "error", "message": str(e)}

    claude_path = shutil.which(settings.claude_code_path)
    if claude_path:
        try:
            proc = await asyncio.create_subprocess_exec(
                settings.claude_code_path, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
            checks["claude_cli"] = {
                "status": "ok",
                "path": claude_path,
                "version": stdout.decode().strip(),
            }
        except (TimeoutError, OSError):
            checks["claude_cli"] = {"status": "error", "message": "실행 실패"}
    else:
        checks["claude_cli"] = {
            "status": "error",
            "message": f"'{settings.claude_code_path}' 경로를 찾을 수 없음",
        }

    mmdc_path = shutil.which("mmdc")
    checks["mermaid_cli"] = (
        {"status": "ok", "path": mmdc_path}
        if mmdc_path
        else {"status": "warning", "message": "mmdc 미설치 (다이어그램 렌더링 불가)"}
    )

    vault = settings.obsidian_vault_path
    if vault:
        from pathlib import Path
        checks["obsidian_vault"] = (
            {"status": "ok", "path": vault}
            if Path(vault).is_dir()
            else {"status": "warning", "message": f"경로 없음: {vault}"}
        )
    else:
        checks["obsidian_vault"] = {"status": "disabled", "message": "설정 안 됨"}

    overall = "healthy"
    if any(c["status"] == "error" for c in checks.values()):
        overall = "degraded"

    return ApiResponse(
        success=True,
        data={
            "status": overall,
            "timestamp": datetime.now(UTC).isoformat(),
            "version": "0.1.0",
            "checks": checks,
        },
    )

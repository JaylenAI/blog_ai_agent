import asyncio
import json
from collections.abc import AsyncGenerator
from dataclasses import dataclass

from app.claude.parser import StreamEvent, extract_json, parse_stream_line
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class ClaudeResponse:
    text: str
    session_id: str = ""
    cost_usd: float = 0.0


class ClaudeClient:
    def __init__(self, cli_path: str | None = None) -> None:
        self._cli_path = cli_path or settings.claude_code_path

    def _build_args(self, prompt: str) -> list[str]:
        return [self._cli_path, "-p", prompt, "--output-format", "stream-json"]

    async def run(self, prompt: str) -> ClaudeResponse:
        args = self._build_args(prompt)
        logger.info("Claude CLI 실행: %s...", prompt[:80])

        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout_bytes, stderr_bytes = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr_bytes.decode("utf-8", errors="replace")
            logger.error("Claude CLI 실패 (code=%d): %s", process.returncode, error_msg)
            raise RuntimeError(f"Claude CLI failed (exit {process.returncode}): {error_msg}")

        result_text = ""
        session_id = ""
        cost_usd = 0.0

        for line in stdout_bytes.decode("utf-8").splitlines():
            event = parse_stream_line(line)
            if event is None:
                continue
            if event.event_type == "result":
                result_text = event.text
                try:
                    raw = json.loads(line)
                    session_id = raw.get("session_id", "")
                    cost_usd = raw.get("cost_usd", 0.0)
                except json.JSONDecodeError:
                    pass

        return ClaudeResponse(text=result_text, session_id=session_id, cost_usd=cost_usd)

    async def run_json(self, prompt: str) -> dict:
        response = await self.run(prompt)
        return extract_json(response.text)

    async def stream(self, prompt: str) -> AsyncGenerator[StreamEvent, None]:
        args = self._build_args(prompt)
        logger.info("Claude CLI 스트림 시작: %s...", prompt[:80])

        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        assert process.stdout is not None
        async for raw_line in process.stdout:
            decoded = raw_line.decode("utf-8")
            event = parse_stream_line(decoded)
            if event is not None:
                yield event

        await process.wait()

        if process.returncode != 0:
            assert process.stderr is not None
            stderr_bytes = await process.stderr.read()
            error_msg = stderr_bytes.decode("utf-8", errors="replace")
            raise RuntimeError(f"Claude CLI stream failed: {error_msg}")

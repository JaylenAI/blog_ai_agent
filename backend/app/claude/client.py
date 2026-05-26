import asyncio
import json
from collections.abc import AsyncGenerator
from dataclasses import dataclass

from app.claude.parser import StreamEvent, extract_json, parse_stream_line
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_TIMEOUT = 300
MAX_RETRIES = 2
RETRY_BASE_DELAY = 2.0


@dataclass(frozen=True)
class ClaudeResponse:
    text: str
    session_id: str = ""
    cost_usd: float = 0.0


class ClaudeClient:
    def __init__(
        self,
        cli_path: str | None = None,
        *,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        self._cli_path = cli_path or settings.claude_code_path
        self._timeout = timeout
        self._max_retries = max_retries

    def _build_args(
        self,
        prompt: str,
        *,
        allowed_tools: list[str] | None = None,
        add_dir: str | None = None,
    ) -> list[str]:
        args = [
            self._cli_path,
            "-p", prompt,
            "--output-format", "stream-json",
            "--verbose",
        ]
        if allowed_tools:
            args.extend(["--allowedTools", ",".join(allowed_tools)])
        if add_dir:
            args.extend(["--add-dir", add_dir])
        return args

    async def _execute(
        self,
        prompt: str,
        *,
        allowed_tools: list[str] | None = None,
        add_dir: str | None = None,
    ) -> ClaudeResponse:
        args = self._build_args(
            prompt, allowed_tools=allowed_tools, add_dir=add_dir
        )

        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=self._timeout
            )
        except TimeoutError:
            process.kill()
            await process.wait()
            raise

        if process.returncode != 0:
            error_msg = stderr_bytes.decode(
                "utf-8", errors="replace"
            )
            raise RuntimeError(
                f"Claude CLI failed (exit {process.returncode})"
                f": {error_msg[:500]}"
            )

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

        return ClaudeResponse(
            text=result_text,
            session_id=session_id,
            cost_usd=cost_usd,
        )

    async def run(
        self,
        prompt: str,
        *,
        timeout: int | None = None,
        allowed_tools: list[str] | None = None,
        add_dir: str | None = None,
    ) -> ClaudeResponse:
        logger.info("Claude CLI 실행: %s...", prompt[:80])
        saved_timeout = self._timeout
        if timeout is not None:
            self._timeout = timeout

        try:
            last_error: Exception | None = None
            for attempt in range(self._max_retries + 1):
                try:
                    return await self._execute(
                        prompt,
                        allowed_tools=allowed_tools,
                        add_dir=add_dir,
                    )
                except TimeoutError:
                    last_error = TimeoutError(
                        f"Claude CLI 타임아웃 ({self._timeout}초)"
                    )
                    logger.warning(
                        "Claude CLI 타임아웃 (시도 %d/%d)",
                        attempt + 1,
                        self._max_retries + 1,
                    )
                except RuntimeError as e:
                    last_error = e
                    logger.warning(
                        "Claude CLI 실패 (시도 %d/%d): %s",
                        attempt + 1,
                        self._max_retries + 1,
                        e,
                    )

                if attempt < self._max_retries:
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    await asyncio.sleep(delay)

            raise last_error or RuntimeError("Claude CLI 실행 실패")
        finally:
            self._timeout = saved_timeout

    async def run_json(
        self,
        prompt: str,
        *,
        timeout: int | None = None,
        allowed_tools: list[str] | None = None,
        add_dir: str | None = None,
    ) -> dict:
        response = await self.run(
            prompt,
            timeout=timeout,
            allowed_tools=allowed_tools,
            add_dir=add_dir,
        )
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

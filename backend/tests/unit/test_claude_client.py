from unittest.mock import AsyncMock, patch

import pytest

from app.claude.client import (
    DEFAULT_TIMEOUT,
    MAX_RETRIES,
    ClaudeClient,
    ClaudeResponse,
)


def test_default_values() -> None:
    client = ClaudeClient()
    assert client._timeout == DEFAULT_TIMEOUT
    assert client._max_retries == MAX_RETRIES


def test_custom_values() -> None:
    client = ClaudeClient(
        cli_path="/custom/claude",
        timeout=120,
        max_retries=5,
    )
    assert client._cli_path == "/custom/claude"
    assert client._timeout == 120
    assert client._max_retries == 5


def test_build_args() -> None:
    client = ClaudeClient(cli_path="/usr/bin/claude")
    args = client._build_args("hello world")
    assert args[0] == "/usr/bin/claude"
    assert "-p" in args
    assert "hello world" in args
    assert "--output-format" in args
    assert "stream-json" in args
    assert "--verbose" in args


@pytest.mark.asyncio
async def test_execute_success() -> None:
    stdout = b'{"type":"result","result":"hello","session_id":"abc","cost_usd":0.01}\n'
    stderr = b""

    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (stdout, stderr)
    mock_proc.returncode = 0

    client = ClaudeClient(cli_path="claude")
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        result = await client._execute("test prompt")

    assert isinstance(result, ClaudeResponse)
    assert result.text == "hello"
    assert result.session_id == "abc"
    assert result.cost_usd == 0.01


@pytest.mark.asyncio
async def test_execute_nonzero_exit() -> None:
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"", b"error output")
    mock_proc.returncode = 1

    client = ClaudeClient(cli_path="claude")
    with (
        patch("asyncio.create_subprocess_exec", return_value=mock_proc),
        pytest.raises(RuntimeError, match="Claude CLI failed"),
    ):
        await client._execute("test")


@pytest.mark.asyncio
async def test_run_retries_on_timeout() -> None:
    call_count = 0

    async def _fake_execute(self, prompt):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise TimeoutError("timeout")
        return ClaudeResponse(text="ok")

    client = ClaudeClient(cli_path="claude", timeout=10, max_retries=2)
    with (
        patch.object(ClaudeClient, "_execute", _fake_execute),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        result = await client.run("test")

    assert result.text == "ok"
    assert call_count == 2


@pytest.mark.asyncio
async def test_run_retries_on_runtime_error() -> None:
    call_count = 0

    async def _fake_execute(self, prompt):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise RuntimeError("CLI crash")
        return ClaudeResponse(text="recovered")

    client = ClaudeClient(cli_path="claude", timeout=10, max_retries=2)
    with (
        patch.object(ClaudeClient, "_execute", _fake_execute),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        result = await client.run("test")

    assert result.text == "recovered"
    assert call_count == 3


@pytest.mark.asyncio
async def test_run_exhausts_retries() -> None:
    async def _fake_execute(self, prompt):
        raise RuntimeError("always fails")

    client = ClaudeClient(cli_path="claude", timeout=10, max_retries=1)
    with (
        patch.object(ClaudeClient, "_execute", _fake_execute),
        patch("asyncio.sleep", new_callable=AsyncMock),
        pytest.raises(RuntimeError, match="always fails"),
    ):
        await client.run("test")


@pytest.mark.asyncio
async def test_run_timeout_override() -> None:
    async def _fake_execute(self, prompt):
        return ClaudeResponse(text="ok")

    client = ClaudeClient(cli_path="claude", timeout=300)
    with patch.object(ClaudeClient, "_execute", _fake_execute):
        result = await client.run("test", timeout=60)

    assert result.text == "ok"
    assert client._timeout == 300


@pytest.mark.asyncio
async def test_run_json_parses_response() -> None:
    async def _fake_execute(self, prompt):
        return ClaudeResponse(text='{"key": "value"}')

    client = ClaudeClient(cli_path="claude")
    with patch.object(ClaudeClient, "_execute", _fake_execute):
        result = await client.run_json("test")

    assert result == {"key": "value"}

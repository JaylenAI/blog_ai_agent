import pytest

from app.claude.parser import extract_json, parse_stream_line


def test_parse_assistant_event() -> None:
    line = '{"type":"assistant","subtype":"text","text":"hello world"}'
    event = parse_stream_line(line)

    assert event is not None
    assert event.event_type == "assistant"
    assert event.subtype == "text"
    assert event.text == "hello world"


def test_parse_result_event() -> None:
    line = '{"type":"result","subtype":"success","result":"final output"}'
    event = parse_stream_line(line)

    assert event is not None
    assert event.event_type == "result"
    assert event.text == "final output"


def test_parse_system_event() -> None:
    line = '{"type":"system","subtype":"init","session_id":"abc"}'
    event = parse_stream_line(line)

    assert event is not None
    assert event.event_type == "system"
    assert event.text == ""


def test_parse_empty_line() -> None:
    assert parse_stream_line("") is None
    assert parse_stream_line("  ") is None


def test_parse_invalid_json() -> None:
    assert parse_stream_line("not json at all") is None


def test_extract_json_direct() -> None:
    result = extract_json('{"slug": "what-is-ai", "title": "테스트"}')
    assert result["slug"] == "what-is-ai"


def test_extract_json_from_code_block() -> None:
    text = 'Here is the analysis:\n```json\n{"slug": "test"}\n```\nDone.'
    result = extract_json(text)
    assert result["slug"] == "test"


def test_extract_json_from_code_block_no_lang() -> None:
    text = '```\n{"key": "value"}\n```'
    result = extract_json(text)
    assert result["key"] == "value"


def test_extract_json_embedded_in_text() -> None:
    text = 'Some preamble text {"slug": "embedded"} and more text'
    result = extract_json(text)
    assert result["slug"] == "embedded"


def test_extract_json_array() -> None:
    text = 'Results: [1, 2, 3]'
    result = extract_json(text)
    assert result == [1, 2, 3]


def test_extract_json_raises_on_no_json() -> None:
    with pytest.raises(ValueError, match="No valid JSON"):
        extract_json("absolutely no json here")


def test_extract_json_whitespace() -> None:
    result = extract_json('  \n  {"key": "val"}  \n  ')
    assert result["key"] == "val"

import json
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class StreamEvent:
    event_type: str
    subtype: str
    text: str


def parse_stream_line(line: str) -> StreamEvent | None:
    line = line.strip()
    if not line:
        return None

    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None

    event_type = data.get("type", "")
    subtype = data.get("subtype", "")

    if event_type == "assistant":
        text = data.get("text", "")
        if not text:
            message = data.get("message", {})
            content = message.get("content", [])
            if content and isinstance(content, list):
                text = content[0].get("text", "")
        return StreamEvent(
            event_type=event_type, subtype=subtype, text=text
        )
    if event_type == "result":
        return StreamEvent(event_type=event_type, subtype=subtype, text=data.get("result", ""))

    return StreamEvent(event_type=event_type, subtype=subtype, text="")


def extract_json(text: str) -> dict:
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    for start_char, end_char in [("{", "}"), ("[", "]")]:
        first = text.find(start_char)
        last = text.rfind(end_char)
        if first != -1 and last > first:
            try:
                return json.loads(text[first : last + 1])
            except json.JSONDecodeError:
                continue

    raise ValueError(f"No valid JSON found in response: {text[:200]}")

from app.pipeline.base import StageInput
from app.pipeline.gates.gate_two import GateTwoStage

MOCK_VALIDATION_DATA = {
    "validations": [
        {"category": "style", "item": "분량", "passed": True},
    ],
    "summary": {"total": 1, "passed": 1, "failed": 0, "score": 1.0},
}


def _make_input(data: dict | None = None) -> StageInput:
    return StageInput(
        article_id=1,
        slug="ai란-무엇인가",
        topic="AI란 무엇인가?",
        data=data or MOCK_VALIDATION_DATA,
    )


async def test_gate_two_name() -> None:
    gate = GateTwoStage()
    assert gate.name == "gate_two"


async def test_gate_two_always_pauses() -> None:
    gate = GateTwoStage()
    result = await gate.execute(_make_input())

    assert result.success is True
    assert result.data.get("gate_pending") is True


async def test_gate_two_passes_validation_data() -> None:
    gate = GateTwoStage()
    result = await gate.execute(_make_input())

    assert result.data["validations"] == MOCK_VALIDATION_DATA["validations"]
    assert result.data["summary"] == MOCK_VALIDATION_DATA["summary"]


async def test_gate_two_empty_data() -> None:
    gate = GateTwoStage()
    result = await gate.execute(_make_input(data={}))

    assert result.success is True
    assert result.data.get("gate_pending") is True

from app.pipeline.base import StageInput
from app.pipeline.gates.gate_one import GateOneStage

MOCK_OUTLINE_DATA = {
    "outline": [
        {"section_number": 1, "heading": "1. 들어가며"},
        {"section_number": 7, "heading": "7. 마치며"},
    ],
    "total_sections": 7,
    "estimated_total_words": 7000,
}


def _make_input(data: dict | None = None) -> StageInput:
    return StageInput(
        article_id=1,
        slug="ai란-무엇인가",
        topic="AI란 무엇인가?",
        data=data or MOCK_OUTLINE_DATA,
    )


async def test_gate_one_name() -> None:
    gate = GateOneStage()
    assert gate.name == "gate_one"


async def test_gate_one_pauses_by_default() -> None:
    gate = GateOneStage()
    result = await gate.execute(_make_input())

    assert result.success is True
    assert result.data.get("gate_pending") is True
    assert result.stage_name == "gate_one"


async def test_gate_one_auto_approve() -> None:
    gate = GateOneStage(auto_approve=True)
    result = await gate.execute(_make_input())

    assert result.success is True
    assert result.data.get("gate_pending") is None
    assert result.data["total_sections"] == 7


async def test_gate_one_passes_data_through_on_auto() -> None:
    gate = GateOneStage(auto_approve=True)
    result = await gate.execute(_make_input())

    assert result.data["outline"] == MOCK_OUTLINE_DATA["outline"]
    assert result.data["estimated_total_words"] == 7000


async def test_gate_one_includes_data_on_pause() -> None:
    gate = GateOneStage(auto_approve=False)
    result = await gate.execute(_make_input())

    assert result.data["gate_pending"] is True
    assert result.data["outline"] == MOCK_OUTLINE_DATA["outline"]
    assert result.data["total_sections"] == 7


async def test_gate_one_empty_data() -> None:
    gate = GateOneStage()
    result = await gate.execute(_make_input(data={}))

    assert result.success is True
    assert result.data.get("gate_pending") is True

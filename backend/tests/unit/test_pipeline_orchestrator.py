from unittest.mock import AsyncMock, MagicMock

from app.pipeline.base import PipelineEvent, ProgressCallback, Stage, StageInput, StageOutput
from app.pipeline.orchestrator import PipelineOrchestrator


class FakeStage(Stage):
    def __init__(self, stage_name: str, output: StageOutput) -> None:
        self._name = stage_name
        self._output = output

    @property
    def name(self) -> str:
        return self._name

    async def execute(
        self,
        stage_input: StageInput,
        on_progress: ProgressCallback | None = None,
    ) -> StageOutput:
        return self._output


class FailingStage(Stage):
    @property
    def name(self) -> str:
        return "router"

    async def execute(
        self,
        stage_input: StageInput,
        on_progress: ProgressCallback | None = None,
    ) -> StageOutput:
        raise RuntimeError("Stage exploded")


def _mock_pipeline_run() -> MagicMock:
    run = MagicMock()
    run.article_id = 1
    run.status = None
    run.started_at = None
    run.completed_at = None
    run.current_stage = None
    run.error_message = ""
    return run


def _mock_session() -> AsyncMock:
    return AsyncMock()


async def _collect_events(
    orchestrator: PipelineOrchestrator,
    topic: str = "테스트 주제",
    slug: str = "test-slug",
) -> list[PipelineEvent]:
    events = []
    async for event in orchestrator.execute(
        pipeline_run=_mock_pipeline_run(),
        topic=topic,
        slug=slug,
        session=_mock_session(),
    ):
        events.append(event)
    return events


async def test_single_stage_success() -> None:
    stage = FakeStage(
        "router",
        StageOutput(stage_name="router", success=True, data={"slug": "test"}),
    )
    events = await _collect_events(PipelineOrchestrator([stage]))

    assert len(events) == 3
    assert events[0].event_type == "stage_start"
    assert events[0].stage == "router"
    assert events[1].event_type == "stage_complete"
    assert events[1].data == {"slug": "test"}
    assert events[2].event_type == "pipeline_complete"


async def test_multi_stage_success() -> None:
    stages = [
        FakeStage("router", StageOutput(stage_name="router", success=True, data={"a": 1})),
        FakeStage(
            "researcher", StageOutput(stage_name="researcher", success=True, data={"b": 2})
        ),
    ]
    events = await _collect_events(PipelineOrchestrator(stages))

    assert len(events) == 5
    assert events[0].event_type == "stage_start"
    assert events[1].event_type == "stage_complete"
    assert events[2].event_type == "stage_start"
    assert events[3].event_type == "stage_complete"
    assert events[4].event_type == "pipeline_complete"


async def test_stage_returns_failure() -> None:
    stage = FakeStage(
        "router",
        StageOutput(stage_name="router", success=False, error="something went wrong"),
    )
    events = await _collect_events(PipelineOrchestrator([stage]))

    assert len(events) == 2
    assert events[0].event_type == "stage_start"
    assert events[1].event_type == "stage_error"
    assert events[1].message == "something went wrong"


async def test_stage_raises_exception() -> None:
    events = await _collect_events(PipelineOrchestrator([FailingStage()]))

    assert len(events) == 2
    assert events[0].event_type == "stage_start"
    assert events[1].event_type == "stage_error"
    assert "Stage exploded" in events[1].message


async def test_pipeline_stops_on_failure() -> None:
    stages = [
        FakeStage("router", StageOutput(stage_name="router", success=False, error="fail")),
        FakeStage(
            "researcher", StageOutput(stage_name="researcher", success=True, data={})
        ),
    ]
    events = await _collect_events(PipelineOrchestrator(stages))

    assert len(events) == 2
    stage_names = [e.stage for e in events]
    assert "researcher" not in stage_names


async def test_gate_pending_pauses_pipeline() -> None:
    gate = FakeStage(
        "gate_one",
        StageOutput(
            stage_name="gate_one",
            success=True,
            data={"gate_pending": True, "outline": [{"heading": "1. 들어가며"}]},
        ),
    )
    generator = FakeStage(
        "generator",
        StageOutput(stage_name="generator", success=True, data={}),
    )

    events = await _collect_events(PipelineOrchestrator([gate, generator]))

    event_types = [e.event_type for e in events]
    assert "gate_pending" in event_types
    assert "pipeline_complete" not in event_types

    started_stages = [e.stage for e in events if e.event_type == "stage_start"]
    assert "generator" not in started_stages


async def test_gate_not_pending_continues() -> None:
    gate = FakeStage(
        "gate_one",
        StageOutput(
            stage_name="gate_one",
            success=True,
            data={"outline": [{"heading": "1. 들어가며"}]},
        ),
    )
    generator = FakeStage(
        "generator",
        StageOutput(stage_name="generator", success=True, data={"done": True}),
    )

    events = await _collect_events(PipelineOrchestrator([gate, generator]))

    event_types = [e.event_type for e in events]
    assert "gate_pending" not in event_types
    assert "pipeline_complete" in event_types


async def test_data_flows_between_stages() -> None:
    received_data: list[dict] = []

    class CapturingStage(Stage):
        @property
        def name(self) -> str:
            return "researcher"

        async def execute(
            self,
            stage_input: StageInput,
            on_progress: ProgressCallback | None = None,
        ) -> StageOutput:
            received_data.append(stage_input.data)
            return StageOutput(stage_name="capture", success=True, data={"captured": True})

    router_output = StageOutput(
        stage_name="router", success=True, data={"from": "router"}
    )
    stages = [
        FakeStage("router", router_output),
        CapturingStage(),
    ]
    await _collect_events(PipelineOrchestrator(stages))

    assert len(received_data) == 1
    assert received_data[0] == {"from": "router"}

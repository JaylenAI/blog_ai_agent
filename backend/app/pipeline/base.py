from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class StageInput:
    article_id: int
    slug: str
    topic: str
    format_id: str = "concept"
    data: dict = field(default_factory=dict)


@dataclass
class StageOutput:
    stage_name: str
    success: bool
    data: dict = field(default_factory=dict)
    error: str = ""


@dataclass
class PipelineEvent:
    event_type: str
    stage: str
    message: str
    data: dict = field(default_factory=dict)


class Stage(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def execute(self, stage_input: StageInput) -> StageOutput: ...

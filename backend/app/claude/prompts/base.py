from abc import ABC, abstractmethod


class PromptTemplate(ABC):
    @abstractmethod
    def render(self, **kwargs: str) -> str: ...

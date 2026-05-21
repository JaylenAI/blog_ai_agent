from app.claude.prompts.base import PromptTemplate
from app.claude.prompts.researcher import OfficialLibrarianPrompt
from app.pipeline.subagents.base import LibrarianSubagent


class OfficialLibrarian(LibrarianSubagent):
    @property
    def name(self) -> str:
        return "librarian-official"

    @property
    def source_type(self) -> str:
        return "official"

    def _get_prompt(self) -> PromptTemplate:
        return OfficialLibrarianPrompt()

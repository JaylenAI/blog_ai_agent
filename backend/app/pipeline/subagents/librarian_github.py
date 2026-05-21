from app.claude.prompts.base import PromptTemplate
from app.claude.prompts.researcher import GithubLibrarianPrompt
from app.pipeline.subagents.base import LibrarianSubagent


class GithubLibrarian(LibrarianSubagent):
    @property
    def name(self) -> str:
        return "librarian-github"

    @property
    def source_type(self) -> str:
        return "github"

    def _get_prompt(self) -> PromptTemplate:
        return GithubLibrarianPrompt()

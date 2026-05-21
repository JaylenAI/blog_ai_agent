from app.claude.prompts.base import PromptTemplate
from app.claude.prompts.researcher import BlogEnLibrarianPrompt
from app.pipeline.subagents.base import LibrarianSubagent


class BlogEnLibrarian(LibrarianSubagent):
    @property
    def name(self) -> str:
        return "librarian-blog-en"

    @property
    def source_type(self) -> str:
        return "blog_en"

    def _get_prompt(self) -> PromptTemplate:
        return BlogEnLibrarianPrompt()

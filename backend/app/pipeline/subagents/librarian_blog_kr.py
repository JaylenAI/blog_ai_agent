from app.claude.prompts.base import PromptTemplate
from app.claude.prompts.researcher import BlogKrLibrarianPrompt
from app.pipeline.subagents.base import LibrarianSubagent


class BlogKrLibrarian(LibrarianSubagent):
    @property
    def name(self) -> str:
        return "librarian-blog-kr"

    @property
    def source_type(self) -> str:
        return "blog_kr"

    def _get_prompt(self) -> PromptTemplate:
        return BlogKrLibrarianPrompt()

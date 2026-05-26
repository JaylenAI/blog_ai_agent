from pydantic import BaseModel


class PublishKitImage(BaseModel):
    name: str
    url: str


class PublishKitDiagram(BaseModel):
    name: str
    content: str


class ReferenceItem(BaseModel):
    url: str
    title: str
    summary: str
    relevance_score: float
    source_type: str


class PublishKit(BaseModel):
    title: str
    category: str
    tags: list[str]
    markdown: str | None
    html: str | None
    images: list[PublishKitImage]
    diagrams: list[PublishKitDiagram]
    references: list[ReferenceItem]
    thumbnail_url: str | None
    word_count: int
    status: str

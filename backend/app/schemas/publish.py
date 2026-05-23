from pydantic import BaseModel


class PublishKitImage(BaseModel):
    name: str
    url: str


class PublishKitDiagram(BaseModel):
    name: str
    content: str


class PublishKit(BaseModel):
    title: str
    category: str
    tags: list[str]
    markdown: str | None
    html: str | None
    images: list[PublishKitImage]
    diagrams: list[PublishKitDiagram]
    word_count: int
    status: str

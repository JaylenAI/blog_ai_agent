from __future__ import annotations

from pydantic import BaseModel, Field


class RangeSpec(BaseModel):
    min: int = 0
    max: int = 99


class CharCountSpec(BaseModel):
    standard: tuple[int, int] = (6000, 8000)
    long: tuple[int, int] = (10000, 13000)


class StructureSpec(BaseModel):
    intro_style: str = ""
    closing_style: str = ""
    required_sections: list[str] = Field(default_factory=list)
    optional_sections: list[str] = Field(default_factory=list)
    section_count: RangeSpec = Field(default_factory=lambda: RangeSpec(min=7, max=9))
    char_count: CharCountSpec = Field(default_factory=CharCountSpec)


class ElementSpec(BaseModel):
    tables_min: int = 1
    code_blocks: tuple[int, int] = (2, 5)
    diagram_types: list[str] = Field(default_factory=list)
    expected_images: tuple[int, int] = (2, 4)
    use_metaphors: bool = False
    use_callout_boxes: bool = True


class ValidationSpec(BaseModel):
    intro_keywords: list[str] = Field(default_factory=lambda: ["들어가며"])
    closing_keywords: list[str] = Field(default_factory=lambda: ["마치며"])
    forbidden_sections: list[str] = Field(
        default_factory=lambda: ["FAQ", "참고 자료", "References"]
    )


class SeoSpec(BaseModel):
    title_max_chars: int = 60
    tags_count: int = 10
    title_patterns: list[str] = Field(default_factory=list)


class FormatSpec(BaseModel):
    id: str
    name: str
    name_en: str = ""
    description: str = ""
    icon: str = ""
    structure: StructureSpec = Field(default_factory=StructureSpec)
    elements: ElementSpec = Field(default_factory=ElementSpec)
    validation: ValidationSpec = Field(default_factory=ValidationSpec)
    seo: SeoSpec = Field(default_factory=SeoSpec)
    prompt_instructions: str = ""
    router_signals: list[str] = Field(default_factory=list)


class FormatSummary(BaseModel):
    id: str
    name: str
    name_en: str
    description: str
    icon: str
    section_count_min: int
    section_count_max: int
    char_count_standard: tuple[int, int]


class FormatSuggestion(BaseModel):
    format_id: str
    name: str
    icon: str
    confidence: float
    reason: str

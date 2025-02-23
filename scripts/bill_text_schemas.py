from __future__ import annotations

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel
from pydantic.fields import Field


class ContentBlockType(str, Enum):
    TITLE = "title"
    DIVISION = "division"
    SECTION = "section"
    SUBSECTION = "subsection"

    PARAGRAPH = "paragraph"
    DEFINITION = "definition"
    LIST_ITEM = "list-item"
    AMENDMENT = "amendment"

    REFERENCE = "reference"
    ANNOTATION = "annotation"


class AnnotationBlock(BaseModel):
    id: str
    content: str = ""


class ContentBlock(BaseModel):
    id: str
    type: ContentBlockType
    text: str
    content: List[ContentBlock] = Field(default_factory=list)
    indent_level: int = 0
    annotations: List[AnnotationBlock] = Field(default_factory=list)
    y_position: Optional[float] = None


class StructuredBillText(BaseModel):
    """Complete structured representation of a parsed bill."""

    title: str = Field("", alias="longTitle")
    content: List[ContentBlock] = Field(default_factory=list)

    class Config:
        populate_by_name = True

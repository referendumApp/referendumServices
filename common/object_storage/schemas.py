from __future__ import annotations

from enum import Enum
from typing import List
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


class StructuredBillText(BaseModel):
    title: str
    content: List[ContentBlock] = Field(default_factory=list)

from __future__ import annotations

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel
from pydantic.fields import Field


class ContentBlockType(str, Enum):
    TEXT = "text"  # Regular paragraph text
    SECTION = "section"  # Major section headers (e.g., "SECTION 1.")
    DIVISION = "division"  # Division markers (e.g., "DIVISION A")


class FontInfo(BaseModel):
    size: Optional[float] = None
    name: Optional[str] = None
    bold: bool = False


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

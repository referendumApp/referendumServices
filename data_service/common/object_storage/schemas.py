from __future__ import annotations

from enum import Enum
from typing import List, Optional
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

    title: str = Field("")
    content: List[ContentBlock] = Field(default_factory=list)

    def get_plain_text(self) -> str:
        """Convert structured bill text to plain text format for backward compatibility."""
        text_parts = []

        if self.title:
            text_parts.append(self.title)
            text_parts.append("\n\n")

        def process_content_blocks(blocks, base_indent_level=0):
            """Recursively process the blocks"""
            for block in blocks:
                indent = "  " * (base_indent_level + block.indent_level)
                if block.text:
                    text_parts.append(f"{indent}{block.text}")
                    text_parts.append("\n")

                if block.content:
                    process_content_blocks(
                        block.content, base_indent_level + block.indent_level + 1
                    )
            if blocks:
                text_parts.append("\n")

        process_content_blocks(self.content)

        return "".join(text_parts)

import io
import re
import requests
import uuid
from collections import Counter
from pathlib import Path
from typing import Dict, Union, List, Optional, Tuple

from pydantic import BaseModel
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTTextLine, LTChar

from common.aws.s3.schemas import (
    ContentBlock,
    ContentBlockType,
    StructuredBillText,
    AnnotationBlock,
)


class FontInfo(BaseModel):
    """Font metadata extracted from PDF elements."""

    size: Optional[float] = None
    name: Optional[str] = None
    bold: bool = False

    @classmethod
    def from_pdf_element(cls, element: LTTextContainer) -> "FontInfo":
        """Extract font information from a PDF text container."""
        font_info = cls()

        for text_line in element._objs:
            if isinstance(text_line, LTTextLine):
                for char in text_line:
                    if isinstance(char, LTChar):
                        font_info.size = char.size
                        font_info.name = char.fontname
                        font_info.bold = "Bold" in char.fontname
                        return font_info
        return font_info


class TextElement(BaseModel):
    """A positioned text element with font information."""

    text: str
    x0: float  # Left position
    y0: float  # Bottom position
    x1: float  # Right position
    y1: float  # Top position
    font: FontInfo

    @property
    def is_section_header(self) -> bool:
        """Check if text matches section header pattern and formatting."""
        section_pattern = r"^SEC(?:TION)?\.?\s*\d+\."
        return bool(re.match(section_pattern, self.text, re.IGNORECASE)) and (
            self.font.bold or (self.font.size and self.font.size > 10)
        )

    @property
    def is_division_header(self) -> bool:
        """Check if text appears to be a division header."""
        return self.text.strip().startswith("DIVISION") and self.font.bold


class BillPDFParser:
    """Extracts structured content from legislative PDFs."""

    # Configurable parsing parameters
    PAGE_WIDTH = 612  # Standard US Letter width in points
    INDENT_STEP = 20  # Points per indent level
    MAX_ANNOTATION_DISTANCE = 30  # Maximum distance to match annotations
    MAX_INDENT = 10  # Maximum allowed indent level
    MIN_CONTENT_LENGTH = 10  # Minimum length for main content

    def __init__(self, source: str | io.BytesIO, start_page_idx: int = 0) -> None:
        if isinstance(source, str):
            if source.startswith("http://") or source.startswith("https://"):
                response = requests.get(source)
                self.pdf_bytes = io.BytesIO(response.content)
                self.pdf_path = None
            else:
                self.pdf_path = Path(source)
                self.pdf_bytes = None
        else:
            self.pdf_bytes = source

        self.start_page_idx = start_page_idx

        # Initialize parser state
        self.bill_data = StructuredBillText()
        self.pages_content: List[List[TextElement]] = []
        self.page_margins: Dict[int, float] = {}

        self._extract_pdf_content()
        self._calculate_page_margins()

    def parse(self) -> StructuredBillText:
        """Parse the full bill into structured data."""
        self._parse_header()
        self._parse_sections()
        return self.bill_data

    def _extract_pdf_content(self) -> None:
        """Extract all text elements and their positioning from the PDF."""
        source = self.pdf_bytes if self.pdf_bytes is not None else self.pdf_path
        pages = extract_pages(source)

        for page_layout in pages:
            page_elements = []

            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text = element.get_text().strip()
                    if text:
                        text_element = TextElement(
                            text=text,
                            x0=element.bbox[0],
                            y0=element.bbox[1],
                            x1=element.bbox[2],
                            y1=element.bbox[3],
                            font=FontInfo.from_pdf_element(element),
                        )
                        page_elements.append(text_element)

            self.pages_content.append(page_elements)

    def _calculate_page_margins(self) -> None:
        """Determine the base left margin for each page."""
        for page_idx, page in enumerate(self.pages_content):
            if not page:
                continue

            # Filter for main content elements
            content_elements = [
                elem
                for elem in page
                if len(elem.text) > self.MIN_CONTENT_LENGTH
                and not self._is_metadata(elem)
                and not self._is_side_annotation(elem, page)
            ]

            if content_elements:
                # Use most common left margin as the base
                left_margins = [int(elem.x0) for elem in content_elements]
                self.page_margins[page_idx] = Counter(left_margins).most_common(1)[0][0]

    def _is_metadata(self, element: TextElement) -> bool:
        """Identify page metadata like numbers and stats."""
        text = element.text
        is_stat = bool(re.match(r"^\d+\s+STAT\.\s+\d+$", text, re.IGNORECASE))
        is_page_num = element.x0 > (self.PAGE_WIDTH * 0.8) and re.match(r"^\d+$", text)
        return is_stat or is_page_num

    def _is_side_annotation(
        self, text_element: TextElement, page_elements: List[TextElement]
    ) -> bool:
        """Determine if element is a margin annotation based on positioning."""
        if len(page_elements) <= 1:
            return False

        # Calculate mode edges for main content
        content_elements = [
            elem for elem in page_elements if len(elem.text) > self.MIN_CONTENT_LENGTH
        ]
        if not content_elements:
            return False

        left_edges = [int(elem.x0) for elem in content_elements]
        right_edges = [int(elem.x1) for elem in content_elements]

        mode_left = Counter(left_edges).most_common(1)[0][0]
        mode_right = Counter(right_edges).most_common(1)[0][0]

        return text_element.x1 <= mode_left or text_element.x0 >= mode_right

    def _calculate_indent_level(self, text_element: TextElement, page_idx: int) -> int:
        """Calculate indent level relative to page's base margin."""
        if text_element.is_section_header:
            return 0

        base_margin = self.page_margins.get(page_idx, self.INDENT_STEP)
        relative_margin = text_element.x0 - base_margin
        indent_level = max(0, int(relative_margin / self.INDENT_STEP))

        return min(indent_level, self.MAX_INDENT)

    def _parse_header(self) -> None:
        """Extract bill metadata from the header section."""
        if not self.pages_content:
            return

        start_page = self.pages_content[self.start_page_idx]
        for idx, element in enumerate(start_page):
            if "An Act" not in element.text:
                continue

            title_parts = [element.text]

            # Collect subsequent lines until "Be it enacted"
            for next_elem in start_page[idx + 1 :]:
                if any(phrase in next_elem.text for phrase in ("Be it enacted", "Be  it  enacted")):
                    break

                if not self._is_side_annotation(next_elem, start_page):
                    title_parts.append(next_elem.text)

            title = " ".join(title_parts)
            self.bill_data.title = title.replace("An Act", "").strip()
            break

    def _parse_sections(self) -> None:
        """Parse all sections of the bill."""
        current_section = None
        for page_idx, page in enumerate(
            self.pages_content[self.start_page_idx :], start=self.start_page_idx
        ):
            if not page:
                continue

            try:
                annotation_content, body_content = self._separate_content(page)

                for element in body_content:
                    section = self._process_content_element(element, current_section, page_idx)

                    if section is not None:
                        if current_section and section.id != current_section.id:
                            self.bill_data.content.append(current_section)
                        current_section = section

                if current_section and annotation_content:
                    self._process_annotations(annotation_content, current_section)

            except Exception as e:
                print(f"Warning: Error processing page {page_idx}: {e}")

        if current_section:
            self.bill_data.content.append(current_section)

        self._clean_up_sections()

    def _separate_content(
        self, page: List[TextElement]
    ) -> Tuple[List[TextElement], List[TextElement]]:
        """Separate annotations from main content."""
        annotation_content = []
        main_content = []

        for element in page:
            if self._is_metadata(element):
                continue

            if self._is_side_annotation(element, page):
                annotation_content.append(element)
            else:
                main_content.append(element)

        return annotation_content, main_content

    def _process_content_element(
        self, element: TextElement, current_section: Optional[ContentBlock], page_idx: int
    ) -> Optional[ContentBlock]:
        """Process a content element and update section structure."""
        if element.is_section_header:
            return self._create_section_block(element)

        if current_section is None or not element.text.strip():
            return None

        if element.is_division_header:
            return self._create_division_block(element)

        self._add_content_block(current_section, element, page_idx)
        return current_section

    def _create_section_block(self, element: TextElement) -> ContentBlock:
        """Create a new section block from a section header."""
        match = re.match(r"SEC(?:TION)?\.?\s*(\d+)\.\s*(.+)", element.text, re.IGNORECASE)

        if match:
            section_num, section_text = match.groups()
            return ContentBlock(
                id=f"sec-{section_num}",
                text=f"Section {section_num}. {section_text.strip()}",
                type=ContentBlockType.SECTION,
            )

        return ContentBlock(
            id=f"sec-unknown-{uuid.uuid4().hex[:8]}", text="Section", type=ContentBlockType.SECTION
        )

    def _create_division_block(self, element: TextElement) -> ContentBlock:
        """Create a new division block."""
        return ContentBlock(
            id=f"division-{uuid.uuid4().hex[:8]}",
            text=element.text.strip(),
            type=ContentBlockType.DIVISION,
        )

    def _add_content_block(
        self, section: ContentBlock, element: TextElement, page_idx: int
    ) -> None:
        """Add a content block to the current section."""
        block_id = f"{section.id}-block-{uuid.uuid4().hex[:8]}"
        indent_level = self._calculate_indent_level(element, page_idx)

        content_block = ContentBlock(
            id=block_id,
            type=ContentBlockType.PARAGRAPH,
            text=element.text,
            indent_level=indent_level,
            y_position=element.y0,
        )

        section.content.append(content_block)

    def _process_annotations(
        self, annotation_elements: List[TextElement], section: ContentBlock
    ) -> None:
        """Process and attach annotations to content blocks."""
        for annotation_element in annotation_elements:
            annotation = AnnotationBlock(
                id=f"{section.id}-annotation-{uuid.uuid4().hex[:8]}",
                content=annotation_element.text,
            )
            section.annotations.append(annotation)

            # Attempt to attach to the nearest line in the section
            if section.content:
                closest_block = None
                min_distance = float("inf")

                for block in section.content:
                    if block.y_position is None:
                        continue

                    distance = abs(block.y_position - annotation_element.y0)
                    if distance < min_distance:
                        min_distance = distance
                        closest_block = block

                if closest_block and min_distance < self.MAX_ANNOTATION_DISTANCE:
                    closest_block.annotations.append(annotation)

    def _clean_up_sections(self) -> None:
        """Remove empty sections and temporary data."""
        self.bill_data.content = [block for block in self.bill_data.content if block.content]

"""
Bill Parser - A tool for parsing and analyzing legislative documents.

This module provides functionality to parse PDF bills into structured data,
categorize their content, and generate HTML representations.

Key components:
- BillPDFParser: Extracts and structures content from PDF bills
- BillCategorizer: Categorizes bill content using keyword analysis
- BillHTMLGenerator: Generates HTML representations of parsed bills

Example usage:
    bill_data = parse_bill_pdf("path/to/bill.pdf", "output.html")
"""

from __future__ import annotations

import re
import uuid
import sys
import json
from enum import Enum
from functools import lru_cache
from collections import Counter
from pathlib import Path
from typing import Dict, Union, List, Optional, Tuple

from pydantic import BaseModel, Field
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTTextLine

from categorization_keywords import CATEGORIZATION_KEYWORDS


class ContentBlockType(str, Enum):
    """Types of content blocks found in legislative documents."""

    TEXT = "text"  # Regular paragraph text
    SECTION = "section"  # Major section headers (e.g., "SECTION 1.")
    DIVISION = "division"  # Division markers (e.g., "DIVISION A")


class FontInfo(BaseModel):
    """Font metadata extracted from PDF elements."""

    size: Optional[float] = None
    name: Optional[str] = None
    bold: bool = False

    @classmethod
    def from_pdf_element(cls, element: LTTextContainer) -> "FontInfo":
        """Extract font information from a PDF text container."""
        font_info = cls()

        # Only need to check first character since font usually consistent within element
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


class Annotation(BaseModel):
    """A margin note or annotation."""

    id: str
    type: str = "annotation"
    content: str = ""
    y_position: float = 0


class ContentBlock(BaseModel):
    """A block of content within the bill."""

    id: str
    type: ContentBlockType
    text: str
    content: List[ContentBlock] = Field(default_factory=list)
    indent_level: int = 0
    annotations: List[Annotation] = Field(default_factory=list)
    y_position: Optional[float] = None

    class Config:
        populate_by_name = True


class BillSubcategory(BaseModel):
    """A specific subcategory classification."""

    id: str
    keywords_matched: List[str] = Field(default_factory=list)


class BillCategory(BaseModel):
    """A high-level category with subcategories."""

    id: str
    keywords_matched: List[str] = Field(default_factory=list)
    subcategories: List[BillSubcategory] = Field(default_factory=list)


class BillData(BaseModel):
    """Complete structured representation of a parsed bill."""

    long_title: str = Field("", alias="longTitle")
    content: List[ContentBlock] = Field(default_factory=list)
    categories: List[BillCategory] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class BillCategorizer:
    # TODO - implement this with NLP

    @staticmethod
    def categorize_bill(bill_data: BillData) -> BillData:
        """Enhanced keyword-based categorization with subcategories."""
        text = bill_data.long_title.lower()

        # Track matched keywords for reporting
        matched_terms = {}
        for main_category, subcategories in CATEGORIZATION_KEYWORDS.items():
            for subcategory, terms in subcategories.items():
                for term in terms:
                    if term in text:
                        # Track which subcategory was matched
                        if main_category not in matched_terms:
                            matched_terms[main_category] = {}
                        if subcategory not in matched_terms[main_category]:
                            matched_terms[main_category][subcategory] = []
                        matched_terms[main_category][subcategory].append(term)

        categories = []
        for main_category, subcats in matched_terms.items():
            # For each matched main category
            main_cat_entry = BillCategory(id=main_category, keywords_matched=[], subcategories=[])

            # Add all matched subcategories
            for subcat, terms in subcats.items():
                main_cat_entry.keywords_matched.extend(terms)
                subcat_entry = BillSubcategory(
                    id=subcat,
                    keywords_matched=terms,
                )
                main_cat_entry.subcategories.append(subcat_entry)

            categories.append(main_cat_entry)

        bill_data.categories = categories
        return bill_data


class BillPDFParser:
    """Extracts structured content from legislative PDFs."""

    # Configurable parsing parameters
    PAGE_WIDTH = 612  # Standard US Letter width in points
    INDENT_STEP = 20  # Points per indent level
    MAX_ANNOTATION_DISTANCE = 30  # Maximum distance to match annotations
    MAX_INDENT = 10  # Maximum allowed indent level
    MIN_CONTENT_LENGTH = 10  # Minimum length for main content

    def __init__(self, pdf_path: Union[str, Path]):
        self.pdf_path = Path(pdf_path)
        self.bill_data = BillData()
        self.pages_content: List[List[TextElement]] = []
        self.page_margins: Dict[int, float] = {}
        self.start_page_idx: int = 1

        # Initialize parser state
        self._extract_pdf_content()
        self._calculate_page_margins()

    def parse(self) -> BillData:
        """Parse the full bill into structured data."""
        self._parse_header()
        self._parse_sections()
        return BillCategorizer.categorize_bill(self.bill_data)

    def _extract_pdf_content(self) -> None:
        """Extract all text elements and their positioning from the PDF."""
        pages = extract_pages(self.pdf_path)

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
            self.bill_data.long_title = title.replace("An Act", "").strip()
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
                annotations, content = self._separate_content(page)

                for element in content:
                    section = self._process_content_element(element, current_section, page_idx)

                    if section is not None:
                        if current_section and section.id != current_section.id:
                            self.bill_data.content.append(current_section)
                        current_section = section

                if current_section and annotations:
                    self._process_annotations(annotations, current_section)

            except Exception as e:
                print(f"Warning: Error processing page {page_idx}: {e}")

        if current_section:
            self.bill_data.content.append(current_section)

        self._clean_up_sections()

    def _separate_content(
        self, page: List[TextElement]
    ) -> Tuple[List[TextElement], List[TextElement]]:
        """Separate annotations from main content."""
        annotations = []
        main_content = []

        for element in page:
            if self._is_metadata(element):
                continue

            if self._is_side_annotation(element, page):
                annotations.append(element)
            else:
                main_content.append(element)

        return annotations, main_content

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
            type=ContentBlockType.TEXT,
            text=element.text,
            indent_level=indent_level,
            y_position=element.y0,
        )

        section.content.append(content_block)

    def _process_annotations(self, annotations: List[TextElement], section: ContentBlock) -> None:
        """Process and attach annotations to content blocks."""
        for element in annotations:
            annotation = Annotation(
                id=f"{section.id}-annotation-{uuid.uuid4().hex[:8]}",
                content=element.text,
                y_position=element.y0,
            )

            section.annotations.append(annotation)
            self._match_annotation_to_content(annotation, section)

    def _match_annotation_to_content(self, annotation: Annotation, section: ContentBlock) -> None:
        """Match annotation to nearest content block by position."""
        if not section.content:
            return

        closest_block = None
        min_distance = float("inf")

        for block in section.content:
            if block.y_position is None:
                continue

            distance = abs(block.y_position - annotation.y_position)
            if distance < min_distance:
                min_distance = distance
                closest_block = block

        if closest_block and min_distance < self.MAX_ANNOTATION_DISTANCE:
            closest_block.annotations.append(annotation)

    def _clean_up_sections(self) -> None:
        """Remove empty sections and temporary data."""
        self.bill_data.content = [block for block in self.bill_data.content if block.content]


class BillHTMLGenerator:
    """Generator for creating HTML representations of parsed bills."""

    def __init__(self, bill_data: Dict):
        """Initialize generator with parsed bill data."""
        if not isinstance(bill_data, dict):
            raise TypeError(f"Expected dict, got {type(bill_data)}")
        self.bill_data = bill_data

    def generate_html(self) -> str:
        """Generate complete HTML document for the bill."""
        sections_html = self._generate_sections()
        categories_html = self._generate_categories()

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{self.bill_data.get('long_title', 'Bill Text')}</title>
            {self._get_styles()}
        </head>
        <body>
            <div class="container">
                <h1>{self.bill_data.get('long_title', '')}</h1>
                {categories_html}
                {sections_html}
            </div>
        </body>
        </html>
        """

    def _generate_sections(self) -> str:
        """Generate HTML for all bill sections."""
        sections = self.bill_data.get("content", [])
        return "\n".join(self._generate_section(section) for section in sections)

    @lru_cache(maxsize=1)
    def _get_styles(self) -> str:
        """Generate CSS styles for the bill display (cached for efficiency)."""
        return """
        <style>
            body {
                line-height: 1.5;
                margin: 0;
                padding: 0;
                color: #111827;
            }

            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
            }

            h1 {
                font-size: 1.5rem;
                margin-bottom: 2rem;
            }

            .section {
                margin-bottom: 2rem;
            }

            .section-header {
                font-size: 1.25rem;
                font-weight: bold;
                margin-bottom: 1rem;
            }

            .division-header {
                font-size: 1.4rem;
                font-weight: bold;
                margin-top: 2rem;
                margin-bottom: 1.5rem;
                text-transform: uppercase;
            }

            .bill-content {
                display: grid;
                grid-template-columns: minmax(0, 1fr) 300px;
                gap: 20px;
            }

            .main-text {
                grid-column: 1;
            }

            .annotations-column {
                grid-column: 2;
            }

            .content-block {
                margin-bottom: 1rem;
                position: relative;
            }

            .annotation-block {
                font-size: 0.875rem;
                color: #4B5563;
                background-color: #F3F4F6;
                padding: 0.5rem;
                margin-bottom: 1rem;
                border-left: 3px solid #6366F1;
            }

            .indent-0 { margin-left: 0; }
            .indent-1 { margin-left: 2rem; }
            .indent-2 { margin-left: 4rem; }
            .indent-3 { margin-left: 6rem; }
            .indent-4 { margin-left: 8rem; }
            .indent-5 { margin-left: 10rem; }

            .text-emphasized { font-weight: bold; }
            .text-heading { font-size: 1.125rem; }

            .categories-section {
                margin-bottom: 2rem;
                border-bottom: 1px solid #E5E7EB;
                padding-bottom: 1rem;
            }

            .categories-container {
                display: flex;
                flex-wrap: wrap;
                gap: 1rem;
            }

            .category {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 0.5rem;
                padding: 0.75rem;
                width: calc(33.333% - 1rem);
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
            }

            .category-header {
                margin-bottom: 0.5rem;
                border-bottom: 1px solid #E5E7EB;
                padding-bottom: 0.5rem;
            }

            .category-id {
                font-weight: bold;
                color: #1F2937;
            }

            .subcategories-container {
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
            }

            .subcategory {
                background-color: #F3F4F6;
                padding: 0.5rem;
                border-radius: 0.25rem;
                font-size: 0.875rem;
            }

            .subcategory-id {
                font-weight: 500;
            }

            .subcategory-keywords {
                color: #6B7280;
                font-size: 0.75rem;
            }

            .annotation-placeholder {
                min-height: 1rem;
            }

            /* Handle annotations on small screens */
            @media (max-width: 768px) {
                .bill-content {
                    grid-template-columns: 1fr;
                }

                .annotations-column {
                    grid-column: 1;
                    margin-top: 1rem;
                    border-top: 1px solid #E5E7EB;
                    padding-top: 1rem;
                }

                .annotation-block {
                    margin-left: 1rem;
                }

                .category {
                    width: 100%;
                }
            }
        </style>
        """

    def _generate_section(self, section: Dict) -> str:
        """Generate HTML for a single bill section."""
        content = section.get("content", [])

        # Generate main content and annotation blocks
        main_blocks = []
        annotation_blocks = []

        for block in content:
            if not isinstance(block, dict):
                continue

            main_blocks.append(self._generate_content_block(block))

            # Handle annotations
            annotations = block.get("annotations", [])
            if annotations:
                for annotation in annotations:
                    annotation_blocks.append(
                        self._generate_annotation_block(annotation, block.get("y_position", 0))
                    )
            else:
                annotation_blocks.append('<div class="annotation-placeholder"></div>')

        main_content = "\n".join(main_blocks)
        annotations = "\n".join(annotation_blocks)

        # Generate section header based on type
        if section.get("type") == "division":
            header = self._generate_division_header(section)
        else:
            header = self._generate_section_header(section)

        return f"""
        <div class="section">
            {header}
            <div class="bill-content">
                <div class="main-text">
                    {main_content}
                </div>
                <div class="annotations-column">
                    {annotations}
                </div>
            </div>
        </div>
        """

    def _generate_content_block(self, block: Dict) -> str:
        """Generate HTML for a content block."""
        indent_level = min(block.get("indent_level", 0), 5)
        classes = [f"indent-{indent_level}"]

        # Add additional styling classes based on font properties
        font = block.get("font", {})
        if font.get("bold"):
            classes.append("text-emphasized")
        if font.get("size", 0) > 11:
            classes.append("text-heading")

        return f"""
        <div class="content-block {' '.join(classes)}">
            {block.get('text', '')}
        </div>
        """

    def _generate_annotation_block(self, annotation: Dict, y_position: float) -> str:
        """Generate HTML for an annotation block."""
        content = annotation.get("content", "")
        if not content:
            return '<div class="annotation-placeholder"></div>'

        return f"""
        <div class="annotation-block" data-y-position="{y_position}">
            {content}
        </div>
        """

    def _generate_division_header(self, section: Dict) -> str:
        """Generate HTML for a division header."""
        return f"""
        <div class="division-header">
            {section.get('text', '')}
        </div>
        """

    def _generate_section_header(self, section: Dict) -> str:
        """Generate HTML for a section header."""
        return f"""
        <div class="section-header">
            {section.get('text', '')}
        </div>
        """

    def _generate_categories(self) -> str:
        """Generate HTML for bill categories section."""
        categories = self.bill_data.get("categories", [])
        if not categories:
            return ""

        category_blocks = []
        for category in categories:
            name = category.get("id", "")

            # Generate subcategories HTML
            subcategories = []
            for subcat in category.get("subcategories", []):
                subcat_id = subcat.get("id", "")
                subcategories.append(f'<span class="subcategory">{subcat_id}</span>')

            subcategories_html = ""
            if subcategories:
                subcategories_html = f"""
                <div class="subcategories">
                    {"".join(subcategories)}
                </div>
                """

            category_blocks.append(
                f"""
            <div class="category">
                <span class="category-id">{name}</span>
                {subcategories_html}
            </div>
            """
            )

        return f"""
        <div class="categories-section">
            <h2>Categories</h2>
            <div class="categories-container">
                {"".join(category_blocks)}
            </div>
        </div>
        """


def parse_bill_pdf(
    pdf_path: Union[str, Path], html_output_path: Optional[Union[str, Path]] = None
) -> Dict:
    """
    Parse a legislative PDF and optionally generate HTML visualization.

    Args:
        pdf_path: Path to the input PDF file
        html_output_path: Optional path to save generated HTML

    Returns:
        Dict containing structured bill data
    """
    parser = BillPDFParser(pdf_path)
    bill_data = parser.parse()
    bill_json = bill_data.model_dump()

    if html_output_path:
        try:
            html_generator = BillHTMLGenerator(bill_json)
            html_content = html_generator.generate_html()
            Path(html_output_path).write_text(html_content, encoding="utf-8")
        except Exception as e:
            print(f"Warning: Error generating HTML: {e}", file=sys.stderr)

    return bill_json


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parse bill PDFs into structured data")
    parser.add_argument("pdf_path", help="Path to PDF file to parse")
    args = parser.parse_args()

    try:
        output_json = Path(args.pdf_path).with_suffix(".json")
        output_html = Path(args.pdf_path).with_suffix(".html")

        print(f"Parsing {args.pdf_path}...")
        bill_data = parse_bill_pdf(args.pdf_path, output_html)

        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(bill_data, f, indent=2, ensure_ascii=False)

        print(f"Successfully saved JSON to {output_json}")
        print(f"Successfully saved HTML to {output_html}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

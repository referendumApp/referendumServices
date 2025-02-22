from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Dict, Union, List, Optional, Tuple, Set
import sys
import json
from enum import Enum
from functools import lru_cache
from collections import Counter

from pydantic import BaseModel, Field
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTTextLine

from categorization_keywords import CATEGORIZATION_KEYWORDS


class FontInfo(BaseModel):
    """Store font information from PDF elements."""

    size: Optional[float] = None
    name: Optional[str] = None
    bold: bool = False


class TextElement(BaseModel):
    """Represent a text element with positioning and font information."""

    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    font: FontInfo


class Annotation(BaseModel):
    """Represent a margin annotation."""

    id: str
    type: str = "annotation"
    content: str = ""
    y_position: float = 0
    margin_position: str = "right_margin"


class ContentBlockType(str, Enum):
    """Types of content blocks."""

    TEXT = "text"
    SECTION = "section"
    DIVISION = "division"


class ContentBlock(BaseModel):
    """Represent a parsed content block within a section."""

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
    """Represent a subcategory assigned to a bill."""

    id: str
    keywords_matched: List[str] = Field(default_factory=list)


class BillCategory(BaseModel):
    """Represent a category assigned to a bill."""

    id: str
    keywords_matched: List[str] = Field(default_factory=list)
    subcategories: List[BillSubcategory] = Field(default_factory=list)


class BillData(BaseModel):
    """Store structured bill data."""

    long_title: str = Field("", alias="longTitle")
    content: List[ContentBlock] = Field(default_factory=list)
    categories: List[BillCategory] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class BillCategorizer:
    def __init__(self, use_model=True):
        self.use_model = use_model
        self.classifier = None

        self.categories = [
            "healthcare",
            "education",
            "infrastructure",
            "economy",
            "defense",
            "justice",
            "environment",
        ]

    def categorize_bill(self, bill_data: BillData) -> BillData:
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
    """Parse PDF bills into structured data."""

    # Constants for PDF layout analysis
    PAGE_WIDTH = 612  # Standard letter width in points
    MAIN_TEXT_MARGIN = 50
    INDENT_STEP = 20
    ANNOTATION_MATCH_THRESHOLD = 30
    MIN_LEFT_MARGIN = 40
    SECTION_PATTERN = r"^SEC(?:TION)?\.?\s*\d+\."

    def __init__(self, pdf_path: Union[str, Path]):
        """Initialize parser with path to PDF file.

        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = Path(pdf_path)
        self.bill_data = BillData()
        self.pages_content: List[List[TextElement]] = []
        self._extract_pdf_content()
        self.common_left_margin = self.MIN_LEFT_MARGIN

    def _extract_pdf_content(self) -> None:
        """Extract text and layout information from PDF."""
        all_text_elements = []

        for page_layout in extract_pages(self.pdf_path):
            page_content = []
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text = element.get_text().strip()
                    if text:
                        bbox = element.bbox
                        font_info = self._extract_font_info(element)
                        text_element = TextElement(
                            text=text,
                            x0=bbox[0],
                            y0=bbox[1],
                            x1=bbox[2],
                            y1=bbox[3],
                            font=font_info,
                        )
                        page_content.append(text_element)
                        all_text_elements.append(text_element)
            self.pages_content.append(page_content)

        # Calculate the most common left margin from all text elements
        # This helps normalize inconsistent scanning
        if all_text_elements:
            left_edges = [
                int(elem.x0)
                for elem in all_text_elements
                if len(elem.text) > 10 and not self._is_section_header(elem.text, elem.font)
            ]
            if left_edges:
                self.common_left_margin = max(self.MIN_LEFT_MARGIN, self._get_mode(left_edges))

    @staticmethod
    def _extract_font_info(element) -> FontInfo:
        """Extract font information from PDF element."""
        font_info = FontInfo()

        for obj in element._objs:
            if isinstance(obj, LTTextLine):
                for char in obj:
                    if isinstance(char, LTChar):
                        font_info.size = char.size
                        font_info.name = char.fontname
                        font_info.bold = "Bold" in char.fontname
                        return font_info
        return font_info

    @staticmethod
    def _is_section_header(text: str, font_info: FontInfo) -> bool:
        """Determine if text is a section header based on content and styling."""
        section_pattern = r"^SEC(?:TION)?\.?\s*\d+\."
        return bool(re.match(section_pattern, text, re.IGNORECASE)) and (
            font_info.bold or (font_info.size and font_info.size > 10)
        )

    def _is_page_number(self, text: str, x_position: float) -> bool:
        """Determine if text is likely a page number."""
        # Check for stat page numbers (e.g., "138 STAT. 1724")
        if re.match(r"^\d+\s+STAT\.\s+\d+$", text, re.IGNORECASE):
            return True

        # Check for page numbers aligned to the right margin
        right_aligned = x_position > (self.PAGE_WIDTH * 0.8)
        return right_aligned and re.match(r"^\d+$", text)

    @staticmethod
    def _get_mode(values: List[int]) -> Optional[int]:
        """Calculate the mode (most frequent value) from a list of values."""
        if not values:
            return None

        return Counter(values).most_common(1)[0][0]

    def _is_side_annotation(
        self, text_element: TextElement, page_elements: List[TextElement]
    ) -> bool:
        """Determine if a text element is a side annotation based on edge positioning."""
        if not page_elements or len(page_elements) <= 1:
            return False

        # Calculate mode left edge and mode right edge for main content
        # Use only elements with substantial text to avoid small fragments
        content_elements = [elem for elem in page_elements if len(elem.text) > 10]
        if not content_elements:
            return False

        left_edges = [int(elem.x0) for elem in content_elements]
        right_edges = [int(elem.x1) for elem in content_elements]

        mode_left_edge = self._get_mode(left_edges)
        mode_right_edge = self._get_mode(right_edges)

        if mode_left_edge is None or mode_right_edge is None:
            return False

        # Check edge positioning criteria
        is_left_of_main_text = text_element.x1 <= mode_left_edge
        is_right_of_main_text = text_element.x0 >= mode_right_edge

        return is_left_of_main_text or is_right_of_main_text

    def parse(self) -> BillData:
        """Parse the full bill and return structured data."""
        self._parse_header()
        self._parse_sections()

        # Apply categorization
        categorizer = BillCategorizer(use_model=True)
        categorized_bill = categorizer.categorize_bill(self.bill_data)

        return categorized_bill

    def _parse_header(self) -> None:
        """Extract bill metadata from the header section."""
        if not self.pages_content:
            return

        # TODO - determine which page actually starts the bill, CR_2024.pdf starts on the second
        first_page = self.pages_content[1]

        # Extract title
        for text_element_idx, text_element in enumerate(first_page):
            if "An Act" in text_element.text:
                title_text = text_element.text
                # Get next few lines until "Be it enacted"
                for next_text_element in first_page[text_element_idx + 1 :]:
                    if any(
                        phrase in next_text_element.text
                        for phrase in ("Be it enacted", "Be  it  enacted")
                    ):
                        break
                    if self._is_side_annotation(next_text_element, first_page):
                        continue
                    title_text += " " + next_text_element.text
                self.bill_data.long_title = title_text.replace("An Act", "").strip()
                break

    def _parse_sections(self) -> None:
        """Parse all sections of the bill."""
        current_section = None

        # Skip first page if it's empty or has only metadata
        start_page = 1 if len(self.pages_content) > 1 else 0

        for page_idx, page in enumerate(self.pages_content[start_page:], start=start_page):
            # Skip empty pages
            if not page:
                continue

            try:
                # Separate annotations from main content
                annotations, main_content = self._separate_annotations_and_content(page)

                # Process main content to establish sections and blocks
                for text_element in main_content:
                    section_updated = self._process_content_element(text_element, current_section)

                    # Check if we got a new section
                    new_section_created = section_updated is not None and (
                        current_section is None or section_updated.id != current_section.id
                    )

                    if new_section_created:
                        # New section created
                        if current_section:
                            self.bill_data.content.append(current_section)
                        current_section = section_updated

                # Process annotations and match them to content blocks
                if current_section and annotations:
                    self._process_annotations(annotations, current_section)
            except Exception as e:
                print(f"Warning: Error processing page {page_idx}: {str(e)}")
                continue

        # Add final section
        if current_section:
            self.bill_data.content.append(current_section)

        # Clean up sections
        self._clean_up_sections()

    def _separate_annotations_and_content(
        self, page: List[TextElement]
    ) -> Tuple[List[TextElement], List[TextElement]]:
        """Separate annotations from main content on a page."""
        annotations = []
        main_content = []

        for text_element in page:
            # Skip irrelevant elements
            if self._is_page_number(text_element.text, text_element.x0) or (
                text_element.text.startswith("PUBLIC LAW")
                and any(year in text_element.text for year in ["2024", "2025"])
            ):
                continue

            if self._is_side_annotation(text_element, page):
                annotations.append(text_element)
            else:
                main_content.append(text_element)

        return annotations, main_content

    def _process_content_element(
        self, text_element: TextElement, current_section: Optional[ContentBlock]
    ) -> Optional[ContentBlock]:
        """Process a content element and update the current section."""
        text = text_element.text
        font_info = text_element.font

        if self._is_section_header(text, font_info):
            # Start new section
            section_match = re.match(r"SEC(?:TION)?\.?\s*(\d+)\.\s*(.+)", text, re.IGNORECASE)
            if section_match:
                return ContentBlock(
                    id=f"sec-{section_match.group(1)}",
                    text=f"Section {section_match.group(1)}. {section_match.group(2).strip()}",
                    type=ContentBlockType.SECTION,
                )
            else:
                return ContentBlock(
                    id=f"sec-unknown-{uuid.uuid4().hex[:8]}",
                    text=f"Section",
                    type=ContentBlockType.SECTION,
                )
        elif current_section is not None and text.strip():
            # Skip stat numbers (often appear as page headers/footers)
            if re.match(r"^\d+\s+STAT", text):
                return current_section

            # Check if this is a division header
            if text.strip().startswith("DIVISION") and font_info.bold:
                # Return as a new section
                return ContentBlock(
                    id=f"division-{uuid.uuid4().hex[:8]}",
                    text=text.strip(),
                    type=ContentBlockType.DIVISION,
                )

            # Add content to current section
            try:
                self._add_content_block(current_section, text_element)
            except Exception as e:
                print(f"Warning: Error adding content block: {str(e)}")
                print(f"Content: {text}")

        return current_section

    def _add_content_block(self, section: ContentBlock, text_element: TextElement) -> None:
        """Add a content block to the current section."""
        block_id = f"{section.id}-block-{uuid.uuid4().hex[:8]}"

        # For section headers, always use indent level 0
        # TODO - implement indent level parsing
        if self._is_section_header(text_element.text, text_element.font):
            indent_level = 0
        else:
            indent_level = 0

        # Create content block
        content_block = ContentBlock(
            id=block_id,
            type=ContentBlockType.TEXT,
            text=text_element.text,
            indent_level=indent_level,
            y_position=text_element.y0,
        )

        section.content.append(content_block)

    def _process_annotations(self, annotations: List[TextElement], section: ContentBlock) -> None:
        """Process annotations and match them to content blocks."""
        for annotation_element in annotations:
            annotation_id = f"{section.id}-annotation-{uuid.uuid4().hex[:8]}"
            annotation = Annotation(
                id=annotation_id,
                content=annotation_element.text,
                y_position=annotation_element.y0,
                margin_position="right_margin",
            )

            # Store annotation at section level
            section.annotations.append(annotation)

            # Find the closest content block by Y position
            self._match_annotation_to_content(annotation, section)

    def _match_annotation_to_content(self, annotation: Annotation, section: ContentBlock) -> None:
        """Match an annotation to the closest content block."""
        if not section.content:
            return

        closest_block = None
        min_distance = float("inf")

        for block in section.content:
            if block.y_position is not None:
                distance = abs(block.y_position - annotation.y_position)
                if distance < min_distance:
                    min_distance = distance
                    closest_block = block

        # Only attach if reasonably close
        if closest_block and min_distance < self.ANNOTATION_MATCH_THRESHOLD:
            closest_block.annotations.append(annotation)

    def _clean_up_sections(self) -> None:
        """Clean up empty sections and remove temporary data."""
        self.bill_data.content = [block for block in self.bill_data.content if block.content]


class BillHTMLGenerator:
    """Generate HTML from parsed bill data."""

    def __init__(self, bill_data: Dict):
        """Initialize generator with parsed bill data."""
        if not isinstance(bill_data, dict):
            raise TypeError(f"Expected bill_data to be a dictionary, got {type(bill_data)}")
        self.bill_data = bill_data

    def generate_html(self) -> str:
        """Generate complete HTML document for the bill."""
        if not isinstance(self.bill_data, dict):
            raise TypeError(f"Expected bill_data to be a dictionary, got {type(self.bill_data)}")

        sections = self.bill_data.get("content")
        if not isinstance(sections, list):
            sections = []

        sections_html = "\n".join(self._generate_section(section) for section in sections)

        long_title = self.bill_data.get("long_title", "")

        # Generate categories HTML
        categories_html = self._generate_categories_section(self.bill_data.get("categories", []))

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{long_title or 'Bill Text'}</title>
            {self._generate_styles()}
        </head>
        <body>
            <div class="container">
                <h1>{long_title}</h1>
                {categories_html}
                {sections_html}
            </div>
        </body>
        </html>
        """

    def _generate_categories_section(self, categories):
        """Generate HTML for categories section."""
        if not categories:
            return ""

        categories_html = []
        for category in categories:
            name = category.get("id", "")
            subcategories_html = ""

            # Add subcategories if they exist
            if "subcategories" in category and category["subcategories"]:
                subcats = []
                for subcat in category["subcategories"]:
                    subcat_id = subcat.get("id", "")
                    subcats.append(f'<span class="subcategory">{subcat_id}</span>')

                if subcats:
                    subcategories_html = f"""
                    <div class="subcategories">
                        {"".join(subcats)}
                    </div>
                    """

            categories_html.append(
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
                {"".join(categories_html)}
            </div>
        </div>
        """

    def _generate_categories_section(self, categories):
        """Generate HTML for categories section with subcategories."""
        if not categories:
            return ""

        categories_html = []
        for category in categories:
            category_id = category.get("id", "")
            keywords = category.get("keywords_matched", [])
            subcategories = category.get("subcategories", [])

            # Generate subcategories HTML
            subcategories_html = ""
            if subcategories:
                subcats_list = []
                for subcat in subcategories:
                    subcat_id = subcat.get("id", "")
                    subcat_keywords = subcat.get("keywords_matched", [])

                    # Format keywords as a comma-separated string if present
                    keywords_str = ""
                    if subcat_keywords:
                        keywords_str = f" (matched: {', '.join(subcat_keywords)})"

                    subcats_list.append(
                        f"""<div class="subcategory">
                            <span class="subcategory-id">{subcat_id.replace('_', ' ').title()}</span>
                            <span class="subcategory-keywords">{keywords_str}</span>
                        </div>"""
                    )

                # Wrap all subcategories in a container
                if subcats_list:
                    subcategories_html = f"""
                    <div class="subcategories-container">
                        {"".join(subcats_list)}
                    </div>
                    """

            categories_html.append(
                f"""
                <div class="category">
                    <div class="category-header">
                        <span class="category-id">{category_id.replace('_', ' ').title()}</span>
                    </div>
                    {subcategories_html}
                </div>
                """
            )

        return f"""
        <div class="categories-section">
            <h2>Categories</h2>
            <div class="categories-container">
                {"".join(categories_html)}
            </div>
        </div>
        """

    @staticmethod
    @lru_cache(maxsize=1)
    def _generate_styles() -> str:
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
        """Generate HTML for a bill section."""
        content = section.get("content", [])

        # Collect all blocks and their annotations
        main_content_blocks = []
        annotation_blocks = []

        for block in content:
            if not isinstance(block, dict):
                continue

            # Generate the main content HTML
            main_content_blocks.append(self._generate_main_content(block))

            # If there's an annotation, add it to annotations column
            block_annotations = block.get("annotations")
            if block_annotations:
                y_position = block.get("y_position", 0)
                for block_annotation in block_annotations:
                    annotation_blocks.append(
                        self._generate_annotation_block(block_annotation, y_position)
                    )
            else:
                annotation_blocks.append('<div class="annotation-placeholder"></div>')

        # Join all blocks
        main_content_html = "\n".join(main_content_blocks)
        annotations_html = "\n".join(annotation_blocks)

        section_type = section.get("type", "")
        section_title = section.get("text", "")

        # Handle division headers differently
        if section_type == "division":
            header_html = f"""
            <div class="division-header">
                {section_title}
            </div>
            """
        else:
            header_html = f"""
            <div class="section-header">
                {section_title}
            </div>
            """

        return f"""
        <div class="section">
            {header_html}
            <div class="bill-content">
                <div class="main-text">
                    {main_content_html}
                </div>
                <div class="annotations-column">
                    {annotations_html}
                </div>
            </div>
        </div>
        """

    def _generate_main_content(self, block: Dict) -> str:
        """Generate HTML for the main content of a block (without annotations)."""
        # Generate classes based on properties and indentation
        indent_level = 0
        classes = [f"indent-{min(indent_level, 5)}"]

        # Apply styles based on the text element's font info
        if block.get("font", {}).get("bold", False):
            classes.append("text-emphasized")
        if block.get("font", {}).get("size", 0) > 11:
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
            return ""

        return f"""
        <div class="annotation-block" data-y-position="{y_position}">
            {content}
        </div>
        """


def parse_bill_pdf(pdf_path: Union[str, Path], html_output_path: Union[str, Path] = None) -> Dict:
    """Parse a bill PDF and return structured data.

    Args:
        pdf_path: Path to the PDF file
        html_output_path: Optional path to save generated HTML

    Returns:
        Dict: Structured bill data
    """
    parser = BillPDFParser(pdf_path)
    bill_data = parser.parse()

    bill_json = bill_data.model_dump()
    if html_output_path and bill_data:
        try:
            html_generator = BillHTMLGenerator(bill_json)
            html_content = html_generator.generate_html()
            Path(html_output_path).write_text(html_content, encoding="utf-8")
        except Exception as e:
            print(f"Warning: Error generating HTML: {str(e)}")
            print("Continuing with JSON output generation...")

    return bill_json


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Parse bill PDFs into structured data")
    parser.add_argument("pdf_path", help="Path to PDF file to parse")
    args = parser.parse_args()

    try:
        # Generate default output paths if not specified
        output_json = Path(args.pdf_path).with_suffix(".json")
        output_html = Path(args.pdf_path).with_suffix(".html")

        # Parse bill
        print(f"Parsing {args.pdf_path}...")
        bill_data = parse_bill_pdf(args.pdf_path, output_html)

        # Save JSON output
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(bill_data, f, indent=2, ensure_ascii=False)

        print(f"Successfully saved JSON to {output_json}")
        if output_html:
            print(f"Successfully saved HTML to {output_html}")

    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

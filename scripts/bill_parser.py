import re
import uuid
from pathlib import Path
from typing import Dict, Union, List, Optional, Tuple, Any
import sys
import json
from functools import lru_cache

from pydantic import BaseModel, Field
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTTextBox, LTTextLine


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
    margin_position: str = "right_margin"  # Default to right margin


class ContentBlock(BaseModel):
    """Represent a parsed content block within a section."""

    id: str
    type: str = "text"
    content: str = ""
    indent_level: int = Field(0, alias="indentLevel")
    order_index: int = Field(0, alias="orderIndex")
    properties: List[str] = []
    y_position: Optional[float] = None
    annotation: Optional[Dict] = None

    class Config:
        populate_by_name = True


class Section(BaseModel):
    """Represent a section of the bill."""

    id: str
    number: str
    title: str
    type: str = "section"
    content: List[ContentBlock] = []
    annotations: List[Annotation] = []


class BillData(BaseModel):
    """Store structured bill data."""

    long_title: str = Field("", alias="longTitle")
    sections: List[Section] = []

    class Config:
        populate_by_name = True

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization with customizations."""
        raw_dict = self.model_dump(by_alias=True)

        # Handle nested structures we want to customize beyond model_dump
        for section_idx, section in enumerate(self.sections):
            # Clean up y_position in content blocks
            for block_idx, block in enumerate(section.content):
                if "y_position" in raw_dict["sections"][section_idx]["content"][block_idx]:
                    del raw_dict["sections"][section_idx]["content"][block_idx]["y_position"]

            # Clean up annotations
            for ann_idx in range(len(section.annotations)):
                if "y_position" in raw_dict["sections"][section_idx]["annotations"][ann_idx]:
                    del raw_dict["sections"][section_idx]["annotations"][ann_idx]["y_position"]

        return raw_dict


class BillPDFParser:
    """Parse PDF bills into structured data."""

    # Constants for PDF layout analysis
    PAGE_WIDTH = 612  # Standard letter width in points
    MAIN_TEXT_MARGIN = 50
    INDENT_STEP = 20
    ANNOTATION_MATCH_THRESHOLD = 30

    def __init__(self, pdf_path: Union[str, Path]):
        """Initialize parser with path to PDF file.

        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = Path(pdf_path)
        self.bill_data = BillData()
        self.pages_content: List[List[TextElement]] = []
        self._extract_pdf_content()

    def _extract_pdf_content(self) -> None:
        """Extract text and layout information from PDF."""
        for page_layout in extract_pages(self.pdf_path):
            page_content = []
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text = element.get_text().strip()
                    if text:
                        bbox = element.bbox
                        font_info = self._extract_font_info(element)
                        page_content.append(
                            TextElement(
                                text=text,
                                x0=bbox[0],
                                y0=bbox[1],
                                x1=bbox[2],
                                y1=bbox[3],
                                font=font_info,
                            )
                        )
            self.pages_content.append(page_content)

    @staticmethod
    def _extract_font_info(element) -> FontInfo:
        """Extract font information from PDF element."""
        font_info = FontInfo()

        if isinstance(element, LTTextBox):
            for line in element:
                if isinstance(line, LTTextLine):
                    for char in line:
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

        # Count frequency of each value
        frequency = {}
        for value in values:
            frequency[value] = frequency.get(value, 0) + 1

        # Find the most frequent value
        return max(frequency.items(), key=lambda x: x[1])[0]

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

    def parse(self) -> Dict:
        """Parse the full bill and return structured data."""
        self._parse_header()
        self._parse_sections()
        return self.bill_data.to_dict()

    def _parse_header(self) -> None:
        """Extract bill metadata from the header section."""
        if not self.pages_content or len(self.pages_content) < 2:
            return

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
                    try:
                        section_updated = self._process_content_element(
                            text_element, current_section
                        )
                        # Check if we got a new section (strict comparison)
                        new_section_created = section_updated is not None and (
                            current_section is None or section_updated.id != current_section.id
                        )

                        if new_section_created:
                            # New section created
                            if current_section:
                                self.bill_data.sections.append(current_section)
                            current_section = section_updated
                    except Exception as e:
                        print(
                            f"Warning: Error processing text element on page {page_idx}: {str(e)}"
                        )
                        continue

                # Process annotations and match them to content blocks
                if current_section and annotations:
                    try:
                        self._process_annotations(annotations, current_section)
                    except Exception as e:
                        print(f"Warning: Error processing annotations on page {page_idx}: {str(e)}")
            except Exception as e:
                print(f"Warning: Error processing page {page_idx}: {str(e)}")
                continue

        # Add final section
        if current_section:
            self.bill_data.sections.append(current_section)

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
        self, text_element: TextElement, current_section: Optional[Section]
    ) -> Optional[Section]:
        """Process a content element and update the current section."""
        text = text_element.text
        font_info = text_element.font

        if self._is_section_header(text, font_info):
            # Start new section
            section_match = re.match(r"SEC(?:TION)?\.?\s*(\d+)\.\s*(.+)", text, re.IGNORECASE)
            if section_match:
                return Section(
                    id=f"sec-{section_match.group(1)}",
                    number=section_match.group(1),
                    title=section_match.group(2).strip(),
                    type="section",
                )
            else:
                # Handle case where title might be on the next line
                return Section(
                    id=f"sec-unknown-{uuid.uuid4().hex[:8]}",
                    number="unknown",
                    title="",
                    type="section",
                )
        elif current_section is not None and text.strip():
            # Skip stat numbers (often appear as page headers/footers)
            if re.match(r"^\d+\s+STAT", text):
                return current_section

            # Check if this is a division header
            if text.strip().startswith("DIVISION") and font_info.bold:
                # Return as a new section
                return Section(
                    id=f"division-{uuid.uuid4().hex[:8]}",
                    number="DIVISION",
                    title=text.strip(),
                    type="division",
                )

            # Add content to current section
            try:
                self._add_content_block(current_section, text_element)
            except Exception as e:
                print(f"Warning: Error adding content block: {str(e)}")
                print(f"Content: {text}")

        return current_section

    def _add_content_block(self, section: Section, text_element: TextElement) -> None:
        """Add a content block to the current section."""
        block_id = f"{section.id}-block-{uuid.uuid4().hex[:8]}"

        # Calculate indent level based on x position
        indent_level = max(0, round((text_element.x0 - self.MAIN_TEXT_MARGIN) / self.INDENT_STEP))

        # Determine text properties
        text_properties = []
        if text_element.font.bold:
            text_properties.append("emphasized")
        if text_element.font.size and text_element.font.size > 11:
            text_properties.append("heading")

        # Create content block
        content_block = ContentBlock(
            id=block_id,
            type="text",
            content=text_element.text,
            indentLevel=indent_level,
            orderIndex=len(section.content),
            properties=text_properties,
            y_position=text_element.y0,
        )

        section.content.append(content_block)

    def _process_annotations(self, annotations: List[TextElement], section: Section) -> None:
        """Process annotations and match them to content blocks."""
        for annotation_element in annotations:
            annotation_id = f"{section.id}-annotation-{uuid.uuid4().hex[:8]}"
            annotation = Annotation(
                id=annotation_id,
                content=annotation_element.text,
                y_position=annotation_element.y0,
                margin_position="right_margin",  # Set all annotations to right margin
            )

            # Store annotation at section level
            section.annotations.append(annotation)

            # Find the closest content block by Y position
            self._match_annotation_to_content(annotation, section)

    def _match_annotation_to_content(self, annotation: Annotation, section: Section) -> None:
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
            annotation_dict = {
                "id": annotation.id,
                "type": annotation.type,
                "content": annotation.content,
                "margin_position": "right_margin",  # Force right margin position
            }

            # If block already has an annotation, append to it
            if closest_block.annotation:
                closest_block.annotation["content"] += " " + annotation.content
            else:
                closest_block.annotation = annotation_dict

    def _clean_up_sections(self) -> None:
        """Clean up empty sections and remove temporary data."""
        # Filter out empty sections
        self.bill_data.sections = [
            section for section in self.bill_data.sections if section.content
        ]


class BillHTMLGenerator:
    """Generate HTML from parsed bill data."""

    def __init__(self, bill_data: Dict):
        """Initialize generator with parsed bill data."""
        if not isinstance(bill_data, dict):
            raise TypeError(f"Expected bill_data to be a dictionary, got {type(bill_data)}")
        self.bill_data = bill_data

    def generate_html(self) -> str:
        """Generate complete HTML document for the bill."""
        # Ensure bill_data is a dictionary and has 'sections' key
        if not isinstance(self.bill_data, dict):
            raise TypeError(f"Expected bill_data to be a dictionary, got {type(self.bill_data)}")

        sections = self.bill_data.get("sections", [])
        if not isinstance(sections, list):
            sections = []

        sections_html = "\n".join(self._generate_section(section) for section in sections)

        long_title = self.bill_data.get("longTitle", "")

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
                {sections_html}
            </div>
        </body>
        </html>
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
            annotation = block.get("annotation")
            if annotation:
                y_position = block.get("orderIndex", 0)  # Use order index for alignment
                annotation_blocks.append(self._generate_annotation_block(annotation, y_position))
            else:
                # Add an empty placeholder to maintain alignment
                annotation_blocks.append('<div class="annotation-placeholder"></div>')

        # Join all blocks
        main_content_html = "\n".join(main_content_blocks)
        annotations_html = "\n".join(annotation_blocks)

        section_type = section.get("type", "")
        section_title = section.get("title", "")

        # Handle division headers differently
        if section_type == "division":
            header_html = f"""
            <div class="division-header">
                {section_title}
            </div>
            """
        else:
            section_number = section.get("number", "")
            header_html = f"""
            <div class="section-header">
                SECTION {section_number}. {section_title}
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
        indent_level = block.get("indentLevel", 0)
        classes = [f"indent-{min(indent_level, 5)}"]

        # Apply styles based on the content properties
        properties = block.get("properties", [])
        if properties:
            if "emphasized" in properties:
                classes.append("text-emphasized")
            if "heading" in properties:
                classes.append("text-heading")

        return f"""
        <div class="content-block {' '.join(classes)}">
            {block.get('content', '')}
        </div>
        """

    def _generate_annotation_block(self, annotation: Dict, y_position: int) -> str:
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

    if html_output_path and bill_data:
        try:
            html_content = BillHTMLGenerator(bill_data).generate_html()
            Path(html_output_path).write_text(html_content, encoding="utf-8")
        except Exception as e:
            print(f"Warning: Error generating HTML: {str(e)}")
            print("Continuing with JSON output generation...")

    return bill_data


def main():
    """Main function to process PDFs from command line."""
    import argparse
    import traceback

    parser = argparse.ArgumentParser(description="Parse bill PDFs into structured data and HTML")
    parser.add_argument("pdf_paths", nargs="+", help="Path(s) to PDF file(s) to parse")
    parser.add_argument("--no-html", action="store_true", help="Skip HTML generation")
    parser.add_argument(
        "--output-dir", type=str, default=".", help="Directory to save output files"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    for pdf_path in args.pdf_paths:
        # Generate output paths based on input filename
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            print(f"Error: File not found: {pdf_path}", file=sys.stderr)
            continue

        base_path = pdf_path.stem
        json_output = output_dir / f"{base_path}.json"
        html_output = None if args.no_html else output_dir / f"{base_path}.html"

        try:
            # Parse PDF and generate outputs
            print(f"Processing {pdf_path}...")
            bill_data = parse_bill_pdf(pdf_path, html_output_path=html_output)

            if not bill_data:
                print(f"Warning: No data extracted from {pdf_path}")
                continue

            # Save JSON output
            with open(json_output, "w", encoding="utf-8") as f:
                json.dump(bill_data, f, indent=2, ensure_ascii=False)

            print(f"Successfully processed {pdf_path}")
            print(f"JSON output saved to: {json_output}")
            if html_output and html_output.exists():
                print(f"HTML output saved to: {html_output}")

        except Exception as e:
            print(f"Error processing {pdf_path}: {str(e)}", file=sys.stderr)
            if args.debug:
                traceback.print_exc()
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

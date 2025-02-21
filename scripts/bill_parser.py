import re
import uuid
from pathlib import Path
from typing import Dict, Union, List
import sys
import json

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTTextBox, LTTextLine


class BillPDFParser:
    def __init__(self, pdf_path: Union[str, Path]):
        """Initialize parser with path to PDF file.

        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = Path(pdf_path)
        self.bill_data = {}
        self.current_page = 1
        self.pages_content = []
        self._extract_pdf_content()

    def _extract_pdf_content(self):
        """Extract text and layout information from PDF."""

        # Extract text with positioning
        for page_layout in extract_pages(self.pdf_path):
            page_content = []
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    # Get text with position and font information
                    text = element.get_text().strip()
                    if text:
                        bbox = element.bbox
                        font_info = self._extract_font_info(element)
                        page_content.append(
                            {
                                "text": text,
                                "x0": bbox[0],
                                "y0": bbox[1],
                                "x1": bbox[2],
                                "y1": bbox[3],
                                "font": font_info,
                            }
                        )
            self.pages_content.append(page_content)

    @staticmethod
    def _extract_font_info(element) -> Dict:
        """Extract font information from PDF element."""
        font_info = {"size": None, "name": None, "bold": False}

        if isinstance(element, LTTextBox):
            for line in element:
                if isinstance(line, LTTextLine):
                    for char in line:
                        if isinstance(char, LTChar):
                            font_info["size"] = char.size
                            font_info["name"] = char.fontname
                            font_info["bold"] = "Bold" in char.fontname
                            return font_info
        return font_info

    def _is_section_header(self, text: str, font_info: Dict) -> bool:
        """Determine if text is a section header based on content and styling."""
        section_pattern = r"^SEC(?:TION)?\.?\s*\d+\."
        return bool(re.match(section_pattern, text, re.IGNORECASE)) and (
            font_info.get("bold", False) or font_info.get("size", 0) > 10
        )

    def _is_page_number(self, text: str, x_position: float, page_width: float = 612) -> bool:
        """Determine if text is likely a page number.

        Args:
            text: The text to check
            x_position: X position of the text
            page_width: Width of the page (default 612 points for letter size)
        """
        # Check for stat page numbers (e.g., "138 STAT. 1724")
        if re.match(r"^\d+\s+STAT\.\s+\d+$", text, re.IGNORECASE):
            return True

        # Check for page numbers that are aligned to the right margin
        right_aligned = x_position > (page_width * 0.8)
        if right_aligned and re.match(r"^\d+$", text):
            return True

        return False

    def _get_mode(self, values):
        """Calculate the mode (most frequent value) from a list of values."""
        if not values:
            return None

        # Count frequency of each value
        frequency = {}
        for value in values:
            frequency[value] = frequency.get(value, 0) + 1

        # Find the most frequent value
        max_freq = 0
        mode = None
        for value, freq in frequency.items():
            if freq > max_freq:
                max_freq = freq
                mode = value

        return mode

    def _is_side_annotation(self, text_element: Dict, page_elements: List[Dict]) -> bool:
        """Determine if a text element is a side annotation based on edge positioning.

        An annotation is defined as:
        ((left edge > mode right edge) OR (right edge < mode left edge))
        AND no text between mode right edge and mode left edge

        Args:
            text_element: The text element to check
            page_elements: All elements on the page for context
        """
        if not page_elements or len(page_elements) <= 1:
            return False

        # Calculate mode left edge and mode right edge for main content
        # Use only elements with substantial text to avoid small fragments
        content_elements = [elem for elem in page_elements if len(elem["text"]) > 10]
        if not content_elements:
            return False

        left_edges = [int(elem["x0"]) for elem in content_elements]
        right_edges = [int(elem["x1"]) for elem in content_elements]

        mode_left_edge = self._get_mode(left_edges)
        mode_right_edge = self._get_mode(right_edges)

        if mode_left_edge is None or mode_right_edge is None:
            return False

        # Check edge positioning criteria
        is_left_of_main_text = text_element["x1"] <= mode_left_edge
        is_right_of_main_text = text_element["x0"] >= mode_right_edge

        return is_left_of_main_text or is_right_of_main_text

    def parse(self) -> Dict:
        """Parse the full bill and return structured data."""
        self._parse_header()
        self._parse_sections()
        return self.bill_data

    def _parse_header(self):
        """Extract bill metadata from the header section."""
        first_page = self.pages_content[1]

        # Extract title
        for text_element in first_page:
            if "An Act" in text_element["text"]:
                title_idx = first_page.index(text_element)
                title_text = text_element["text"]
                # Get next few lines until "Be it enacted"
                for next_text_element in first_page[title_idx + 1 :]:
                    if "Be it enacted" in next_text_element["text"]:
                        break
                    if "Be  it  enacted" in next_text_element["text"]:
                        break
                    if self._is_side_annotation(next_text_element, first_page):
                        continue
                    title_text += " " + next_text_element["text"]
                self.bill_data["longTitle"] = title_text.replace("An Act", "").strip()
                break

    # Update the _parse_sections method to properly handle annotations

    def _parse_sections(self):
        """Parse all sections of the bill."""
        self.bill_data["sections"] = []
        current_section = None

        for page_idx, page in enumerate(self.pages_content):
            # First separate annotations from main content
            annotations = []
            main_content = []

            # Filter out page numbers and separate annotations from content
            for text_element in page:
                if self._is_page_number(text_element["text"], text_element["x0"]):
                    continue

                # Skip PUBLIC LAW headers
                if text_element["text"].startswith("PUBLIC LAW") and any(
                    year in text_element["text"] for year in ["2024", "2025"]
                ):
                    continue

                if self._is_side_annotation(text_element, page):
                    annotations.append(text_element)
                else:
                    main_content.append(text_element)

            # Process main content first to establish sections and blocks
            for text_element in main_content:
                text = text_element["text"]
                font_info = text_element["font"]

                if self._is_section_header(text, font_info):
                    # Complete previous section
                    if current_section:
                        self.bill_data["sections"].append(current_section)

                    # Start new section
                    section_match = re.match(
                        r"SEC(?:TION)?\.?\s*(\d+)\.\s*(.+)", text, re.IGNORECASE
                    )
                    if section_match:
                        current_section = {
                            "id": f"sec-{section_match.group(1)}",
                            "number": section_match.group(1),
                            "title": section_match.group(2).strip(),
                            "type": "section",
                            "content": [],
                            "annotations": [],
                        }
                    else:
                        # Handle case where title might be on the next line
                        current_section = {
                            "id": f"sec-unknown-{uuid.uuid4().hex[:8]}",
                            "number": "unknown",
                            "title": "",
                            "type": "section",
                            "content": [],
                            "annotations": [],
                        }
                elif current_section and text.strip():
                    # Skip stat numbers (often appear as page headers/footers)
                    if re.match(r"^\d+\s+STAT", text):
                        continue

                    # Check if this is a division header
                    if text.strip().startswith("DIVISION") and font_info.get("bold", False):
                        # Store as a special section
                        if current_section:
                            self.bill_data["sections"].append(current_section)

                        current_section = {
                            "id": f"division-{uuid.uuid4().hex[:8]}",
                            "number": "DIVISION",
                            "title": text.strip(),
                            "type": "division",
                            "content": [],
                            "annotations": [],
                        }
                        continue

                    # Add content to current section
                    block_id = f"{current_section['id']}-block-{uuid.uuid4().hex[:8]}"

                    # Calculate indent level based on x position relative to page
                    # This helps maintain proper indentation in the output
                    main_text_margin = 50  # typical left margin for main text
                    indent_step = 20  # points per indent level
                    indent_level = max(
                        0, round((text_element["x0"] - main_text_margin) / indent_step)
                    )

                    # Store text formatting information as classification labels
                    # instead of styling directives
                    text_properties = []
                    if font_info["bold"]:
                        text_properties.append("emphasized")

                    if font_info["size"] > 11:
                        text_properties.append("heading")

                    content_block = {
                        "id": block_id,
                        "type": "text",
                        "content": text,
                        "indentLevel": indent_level,
                        "orderIndex": len(current_section["content"]),
                        "properties": text_properties,
                        "y_position": text_element[
                            "y0"
                        ],  # Store Y position for annotation matching
                    }

                    current_section["content"].append(content_block)

            # Now process annotations and match them to content blocks based on Y position
            if current_section and annotations:
                for annotation in annotations:
                    # Create annotation object
                    annotation_y = annotation["y0"]
                    annotation_id = f"{current_section['id']}-annotation-{uuid.uuid4().hex[:8]}"
                    annotation_obj = {
                        "id": annotation_id,
                        "type": "annotation",
                        "content": annotation["text"],
                        "y_position": annotation_y,
                        # Determine if annotation is in left or right margin
                        "margin_position": "left_margin"
                        if annotation["x0"] < 100
                        else "right_margin",
                    }

                    # Store annotation at section level
                    current_section["annotations"].append(annotation_obj)

                    # Find the closest content block by Y position
                    if current_section["content"]:
                        closest_block = None
                        min_distance = float("inf")

                        for block in current_section["content"]:
                            distance = abs(block["y_position"] - annotation_y)
                            if distance < min_distance:
                                min_distance = distance
                                closest_block = block

                        # Only attach if reasonably close (within threshold)
                        if min_distance < 30:  # Threshold in points
                            # If block already has an annotation, append to it
                            if "annotation" in closest_block:
                                closest_block["annotation"]["content"] += (
                                    " " + annotation_obj["content"]
                                )
                            else:
                                closest_block["annotation"] = annotation_obj

        # Add final section
        if current_section:
            self.bill_data["sections"].append(current_section)

        # Clean up empty sections and those that might just be artifacts
        self.bill_data["sections"] = [
            section
            for section in self.bill_data["sections"]
            if section["content"] and len(section["content"]) > 0
        ]

        # Remove temporary y_position from content blocks after processing
        for section in self.bill_data["sections"]:
            for block in section["content"]:
                if "y_position" in block:
                    del block["y_position"]
            if "annotations" in section:
                for annotation in section["annotations"]:
                    if "y_position" in annotation:
                        del annotation["y_position"]


class BillHTMLGenerator:
    def __init__(self, bill_data: Dict):
        """Initialize generator with parsed bill data.

        Args:
            bill_data: Dictionary containing parsed bill structure
        """
        self.bill_data = bill_data

    def _generate_styles(self) -> str:
        """Generate CSS styles for the bill display."""
        return """
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                line-height: 1.5;
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
                color: #111827;
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
            .content-block {
                margin-bottom: 0.5rem;
                position: relative;
            }
            .indent-0 { margin-left: 0; }
            .indent-1 { margin-left: 2rem; }
            .indent-2 { margin-left: 4rem; }
            .indent-3 { margin-left: 6rem; }
            .indent-4 { margin-left: 8rem; }
            .indent-5 { margin-left: 10rem; }
            .text-emphasized { font-weight: bold; }
            .text-heading { font-size: 1.125rem; }
            .annotation {
                font-size: 0.875rem;
                color: #4B5563;
                background-color: #F3F4F6;
                padding: 0.5rem;
                margin-top: 0.25rem;
                margin-bottom: 0.75rem;
                display: block;
            }
            .annotation-left {
                border-left: 3px solid #6366F1; /* Indigo color for left margin */
                margin-right: 2rem;
            }
            .annotation-right {
                border-left: 3px solid #9CA3AF; /* Gray color for right margin */
                margin-left: 2rem;
            }
        </style>
        """

    def _generate_content_block(self, block: Dict) -> str:
        """Generate HTML for a single content block.

        Args:
            block: Dictionary containing block content and styling
        """
        # Generate classes based on properties and indentation
        classes = [f"indent-{min(block['indentLevel'], 5)}"]

        # Apply styles based on the content properties
        if "properties" in block:
            if "emphasized" in block["properties"]:
                classes.append("text-emphasized")
            if "heading" in block["properties"]:
                classes.append("text-heading")

        html = f"""
        <div class="content-block {' '.join(classes)}">
            {block['content']}
        """

        # Add the annotation if it exists
        if "annotation" in block:
            annotation_class = "annotation"
            if block["annotation"].get("margin_position") == "left_margin":
                annotation_class += " annotation-left"
            else:
                annotation_class += " annotation-right"

            html += f"""
            <div class="{annotation_class}">
                {block['annotation']['content']}
            </div>
            """

        html += "</div>"
        return html

    def _generate_section(self, section: Dict) -> str:
        """Generate HTML for a bill section.

        Args:
            section: Dictionary containing section data
        """
        content_html = "\n".join(
            self._generate_content_block(block) for block in section["content"]
        )

        # Handle division headers differently
        if section["type"] == "division":
            return f"""
            <div class="section">
                <div class="division-header">
                    {section['title']}
                </div>
                {content_html}
            </div>
            """
        else:
            return f"""
            <div class="section">
                <div class="section-header">
                    SECTION {section['number']}. {section['title']}
                </div>
                {content_html}
            </div>
            """

    def generate_html(self) -> str:
        """Generate complete HTML document for the bill."""
        sections_html = "\n".join(
            self._generate_section(section) for section in self.bill_data["sections"]
        )

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{self.bill_data.get('longTitle', 'Bill Text')}</title>
            {self._generate_styles()}
        </head>
        <body>
            <h1>{self.bill_data.get('longTitle', '')}</h1>
            {sections_html}
        </body>
        </html>
        """


def generate_bill_html(bill_data: Dict, output_path: Union[str, Path] = None) -> str:
    """Generate HTML from bill data and optionally save to file.

    Args:
        bill_data: Dictionary containing parsed bill structure
        output_path: Optional path to save the HTML file

    Returns:
        str: Generated HTML content
    """
    generator = BillHTMLGenerator(bill_data)
    html_content = generator.generate_html()

    if output_path:
        output_path = Path(output_path)
        output_path.write_text(html_content, encoding="utf-8")

    return html_content


# Update the parse_bill_pdf function to optionally generate HTML
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

    if html_output_path:
        generate_bill_html(bill_data, html_output_path)

    return bill_data


if __name__ == "__main__":
    for pdf_path in ["2024_cr.pdf"]:  # "S2685.pdf"
        # Generate output paths based on input filename
        base_path = Path(pdf_path).stem
        json_output = f"{base_path}.json"
        html_output = f"{base_path}.html"

        try:
            # Parse PDF and generate both outputs
            bill_data = parse_bill_pdf(pdf_path, html_output_path=html_output)

            # Save JSON output
            with open(json_output, "w", encoding="utf-8") as f:
                json.dump(bill_data, f, indent=2, ensure_ascii=False)

            print(f"Successfully processed {pdf_path}")
            print(f"JSON output saved to: {json_output}")
            print(f"HTML output saved to: {html_output}")

        except Exception as e:
            print(f"Error processing {pdf_path}: {str(e)}", file=sys.stderr)
            sys.exit(1)

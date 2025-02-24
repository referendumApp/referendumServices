import sys
import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, Union, Optional

from pipeline.bill_pdf_parser import BillPDFParser


class BillHTMLGenerator:
    """Generator for creating HTML representations of parsed bills."""

    def __init__(self, data: Dict):
        """Initialize generator with parsed bill data."""
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict, got {type(data)}")
        self.data = data

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
            <title>{self.data.get('title', 'Bill Text')}</title>
            {self._get_styles()}
        </head>
        <body>
            <div class="container">
                <h1>{self.data.get('title', '')}</h1>
                {categories_html}
                {sections_html}
            </div>
        </body>
        </html>
        """

    def _generate_sections(self) -> str:
        """Generate HTML for all bill sections."""
        sections = self.data.get("content", [])
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
            block_annotations = block.get("annotations", [])
            if block_annotations:
                for annotation in block_annotations:
                    annotation_blocks.append(self._generate_annotation_block(annotation))
            else:
                annotation_blocks.append('<div class="annotation-placeholder"></div>')

        main_content = "\n".join(main_blocks)
        annotation_content = "\n".join(annotation_blocks)

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
                    {annotation_content}
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

    def _generate_annotation_block(self, annotation: Dict) -> str:
        """Generate HTML for an annotation block."""
        content = annotation.get("content", "")
        if not content:
            return '<div class="annotation-placeholder"></div>'

        return f"""
        <div class="annotation-block">
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
        categories = self.data.get("categories", [])
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
    pdf_path: Union[str, Path],
    start_page_idx: int = 0,
    html_output_path: Optional[Union[str, Path]] = None,
) -> Dict:
    """
    Parse a legislative PDF and optionally generate HTML visualization.

    Args:
        pdf_path: Path to the input PDF file
        html_output_path: Optional path to save generated HTML

    Returns:
        Dict containing structured bill data
    """
    bill_parser = BillPDFParser(pdf_path, start_page_idx)
    parsed_data = bill_parser.parse()
    json_data = parsed_data.model_dump()

    if html_output_path:
        try:
            html_generator = BillHTMLGenerator(json_data)
            html_content = html_generator.generate_html()
            Path(html_output_path).write_text(html_content, encoding="utf-8")
        except Exception as e:
            print(f"Warning: Error generating HTML: {e}", file=sys.stderr)

    return json_data


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parse bill PDFs into structured data")
    parser.add_argument("pdf_path", help="Path to PDF file to parse")
    parser.add_argument("start_page", type=int, help="Page index to start from")
    args = parser.parse_args()

    try:
        output_json = Path(args.pdf_path).with_suffix(".json")
        output_html = Path(args.pdf_path).with_suffix(".html")

        print(f"Parsing {args.pdf_path}...")
        structured_bill_text = parse_bill_pdf(args.pdf_path, args.start_page, output_html)

        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(structured_bill_text, f, indent=2, ensure_ascii=False)

        print(f"Successfully saved JSON to {output_json}")
        print(f"Successfully saved HTML to {output_html}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

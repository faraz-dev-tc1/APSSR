"""
PDF text extraction with spatial coordinates and metadata
"""
import pdfplumber
from typing import List, Dict, Any
from collections import Counter
import hashlib

from src.models.document import TextLine, PageMetadata, DocumentFingerprint, DocumentType
from src.utils.logger import get_logger


logger = get_logger("pdf_extractor")


class PDFExtractor:
    """Extracts text from PDF with spatial and font metadata"""

    def __init__(self):
        """Initialize PDF extractor"""
        self.pages_data = []
        self.text_lines = []

    def extract(self, pdf_path: str) -> tuple[List[PageMetadata], List[TextLine]]:
        """
        Extract text from PDF with metadata

        Args:
            pdf_path: Path to PDF file

        Returns:
            Tuple of (page_metadata_list, text_lines_list)
        """
        logger.info(f"Extracting text from: {pdf_path}")

        pages_metadata = []
        all_text_lines = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    # Extract page metadata
                    page_meta = self._extract_page_metadata(page, page_num)
                    pages_metadata.append(page_meta)

                    # Extract text lines with coordinates
                    text_lines = self._extract_text_lines(page, page_num)
                    all_text_lines.extend(text_lines)

                    logger.debug(f"Page {page_num}: {len(text_lines)} text lines extracted")

            logger.info(f"Extracted {len(all_text_lines)} total text lines from {len(pages_metadata)} pages")
            return pages_metadata, all_text_lines

        except Exception as e:
            logger.error(f"Error extracting PDF: {str(e)}")
            raise

    def _extract_page_metadata(self, page, page_num: int) -> PageMetadata:
        """Extract metadata for a single page"""
        width = page.width
        height = page.height

        # Calculate text density
        text = page.extract_text() or ""
        text_density = len(text.strip()) / (width * height) if width * height > 0 else 0

        return PageMetadata(
            page_number=page_num,
            width=width,
            height=height,
            text_density=text_density
        )

    def _extract_text_lines(self, page, page_num: int) -> List[TextLine]:
        """Extract text lines with spatial and font information"""
        text_lines = []

        try:
            # Extract words with detailed properties
            words = page.extract_words(
                extra_attrs=['fontname', 'size'],
                keep_blank_chars=True
            )

            if not words:
                return text_lines

            # Group words into lines based on y-coordinate
            lines_dict = {}
            for word in words:
                y_pos = round(word['top'], 1)  # Round to group nearby words
                if y_pos not in lines_dict:
                    lines_dict[y_pos] = []
                lines_dict[y_pos].append(word)

            # Process each line
            for y_pos in sorted(lines_dict.keys()):
                line_words = sorted(lines_dict[y_pos], key=lambda w: w['x0'])

                if not line_words:
                    continue

                # Combine words into line
                line_text = ' '.join(word['text'] for word in line_words)

                # Get font properties (use most common)
                font_sizes = [word.get('size', 0) for word in line_words]
                font_names = [word.get('fontname', '') for word in line_words]

                avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 0
                most_common_font = Counter(font_names).most_common(1)[0][0] if font_names else ""

                # Calculate indentation and line height
                first_word = line_words[0]
                indentation = first_word['x0']
                line_height = first_word.get('height', 0)

                # Detect bold/italic from font name
                is_bold = 'bold' in most_common_font.lower()
                is_italic = 'italic' in most_common_font.lower()

                text_line = TextLine(
                    content=line_text.strip(),
                    page_number=page_num,
                    x=first_word['x0'],
                    y=y_pos,
                    font_size=avg_font_size,
                    font_name=most_common_font,
                    line_height=line_height,
                    indentation=indentation,
                    is_bold=is_bold,
                    is_italic=is_italic
                )

                text_lines.append(text_line)

        except Exception as e:
            logger.error(f"Error extracting text lines from page {page_num}: {str(e)}")

        return text_lines

    def generate_fingerprint(
        self,
        pages: List[PageMetadata],
        text_lines: List[TextLine]
    ) -> DocumentFingerprint:
        """
        Generate unique fingerprint for document

        Args:
            pages: List of page metadata
            text_lines: List of text lines

        Returns:
            Document fingerprint
        """
        # Get first 100 characters
        all_text = ' '.join(line.content for line in text_lines[:50])
        first_100 = all_text[:100] if len(all_text) >= 100 else all_text

        # Font size distribution
        font_sizes = [line.font_size for line in text_lines]
        font_size_dist = dict(Counter(round(size, 1) for size in font_sizes))

        # Structure hash
        structure_str = f"{len(pages)}_{len(text_lines)}_{first_100}"
        structure_hash = hashlib.md5(structure_str.encode()).hexdigest()

        # Classify document type (basic heuristic)
        doc_type = self._classify_document_type(text_lines)

        return DocumentFingerprint(
            first_100_chars=first_100,
            font_size_distribution=font_size_dist,
            structure_hash=structure_hash,
            document_type=doc_type,
            total_pages=len(pages)
        )

    def _classify_document_type(self, text_lines: List[TextLine]) -> DocumentType:
        """Classify document type based on content"""
        all_text = ' '.join(line.content for line in text_lines[:100]).lower()

        has_rules = 'rule' in all_text and any(
            'rule ' in line.content.lower() for line in text_lines[:50]
        )

        has_gos = 'g.o' in all_text or 'government order' in all_text

        if has_rules and has_gos:
            return DocumentType.MIXED_DOCUMENT
        elif has_rules:
            return DocumentType.BASE_RULEBOOK
        elif has_gos:
            return DocumentType.AMENDMENT_COLLECTION
        else:
            return DocumentType.BASE_RULEBOOK  # Default

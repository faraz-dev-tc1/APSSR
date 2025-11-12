"""
Noise filtering - removes headers, footers, page numbers, watermarks
"""
import re
from typing import List, Set
from collections import Counter
from src.models.document import TextLine, PageMetadata
from src.utils.logger import get_logger


logger = get_logger("noise_filter")


class NoiseFilter:
    """Filters out noise from extracted text"""

    def __init__(self, repetition_threshold: float = 0.9):
        """
        Initialize noise filter

        Args:
            repetition_threshold: Threshold for detecting repetitive elements (0.0-1.0)
        """
        self.repetition_threshold = repetition_threshold
        self.detected_headers = set()
        self.detected_footers = set()

    def filter(
        self,
        text_lines: List[TextLine],
        pages: List[PageMetadata]
    ) -> List[TextLine]:
        """
        Filter noise from text lines

        Args:
            text_lines: List of text lines
            pages: List of page metadata

        Returns:
            Filtered text lines
        """
        logger.info(f"Filtering noise from {len(text_lines)} text lines")

        # Detect repetitive elements
        self._detect_headers_footers(text_lines, pages)

        # Filter lines
        filtered_lines = []
        for line in text_lines:
            if not self._is_noise(line, pages):
                filtered_lines.append(line)

        logger.info(f"Filtered to {len(filtered_lines)} lines (removed {len(text_lines) - len(filtered_lines)})")
        return filtered_lines

    def _detect_headers_footers(self, text_lines: List[TextLine], pages: List[PageMetadata]):
        """Detect repetitive headers and footers"""
        if not text_lines:
            return

        total_pages = len(pages)

        # Group lines by y-position (top/bottom regions)
        top_region = {}  # y_pos -> [content]
        bottom_region = {}

        for line in text_lines:
            # Determine page height (approximate)
            page_height = 800  # Default, can be refined

            # Top 15% of page
            if line.y < page_height * 0.15:
                y_key = round(line.y, -1)  # Round to nearest 10
                if y_key not in top_region:
                    top_region[y_key] = []
                top_region[y_key].append(line.content)

            # Bottom 15% of page
            elif line.y > page_height * 0.85:
                y_key = round(line.y, -1)
                if y_key not in bottom_region:
                    bottom_region[y_key] = []
                bottom_region[y_key].append(line.content)

        # Find repetitive patterns
        self.detected_headers = self._find_repetitive_patterns(top_region, total_pages)
        self.detected_footers = self._find_repetitive_patterns(bottom_region, total_pages)

        logger.debug(f"Detected {len(self.detected_headers)} header patterns")
        logger.debug(f"Detected {len(self.detected_footers)} footer patterns")

    def _find_repetitive_patterns(
        self,
        region_dict: dict,
        total_pages: int
    ) -> Set[str]:
        """Find patterns that repeat across many pages"""
        patterns = set()

        for y_pos, contents in region_dict.items():
            # Count occurrences of each unique content
            content_counts = Counter(contents)

            for content, count in content_counts.items():
                # If appears on >90% of pages, it's likely header/footer
                if count / total_pages >= self.repetition_threshold:
                    patterns.add(content.strip())

        return patterns

    def _is_noise(self, line: TextLine, pages: List[PageMetadata]) -> bool:
        """Check if a line is noise"""
        content = line.content.strip()

        # Empty line
        if not content:
            return True

        # Too short (likely artifact)
        if len(content) < 3:
            return True

        # Detected header/footer
        if content in self.detected_headers or content in self.detected_footers:
            return True

        # Page number patterns
        if self._is_page_number(content, pages):
            return True

        # Watermark/stamp patterns
        if self._is_watermark(content):
            return True

        return False

    def _is_page_number(self, content: str, pages: List[PageMetadata]) -> bool:
        """Check if content is a page number"""
        # Pure number
        if content.isdigit():
            page_num = int(content)
            if 1 <= page_num <= len(pages) + 10:  # Allow some margin
                return True

        # Common page number formats
        page_patterns = [
            r'^Page\s+\d+$',
            r'^\d+\s+of\s+\d+$',
            r'^-\s*\d+\s*-$',
            r'^\[\d+\]$',
        ]

        for pattern in page_patterns:
            if re.match(pattern, content, re.IGNORECASE):
                return True

        return False

    def _is_watermark(self, content: str) -> bool:
        """Check if content is a watermark or stamp"""
        watermark_keywords = [
            'confidential',
            'draft',
            'copy',
            'original',
            'duplicate',
            'certified',
            'watermark'
        ]

        content_lower = content.lower()

        # Single word watermarks
        if content_lower in watermark_keywords:
            return True

        # Repeated characters (often artifacts)
        if len(set(content)) <= 2 and len(content) > 5:
            return True

        return False

    def remove_scan_artifacts(self, text_lines: List[TextLine]) -> List[TextLine]:
        """Remove common scan artifacts"""
        cleaned_lines = []

        for line in text_lines:
            content = line.content

            # Remove leading/trailing special characters
            content = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', content)

            # Remove excessive whitespace
            content = re.sub(r'\s+', ' ', content)

            # Skip if cleaned content is too short
            if len(content.strip()) < 3:
                continue

            # Update line with cleaned content
            cleaned_line = TextLine(
                content=content.strip(),
                page_number=line.page_number,
                x=line.x,
                y=line.y,
                font_size=line.font_size,
                font_name=line.font_name,
                line_height=line.line_height,
                indentation=line.indentation,
                is_bold=line.is_bold,
                is_italic=line.is_italic
            )

            cleaned_lines.append(cleaned_line)

        return cleaned_lines

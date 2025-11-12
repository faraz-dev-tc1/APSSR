"""
Content normalization - fixes broken words, standardizes formatting
"""
import re
from typing import List
from src.models.document import TextLine
from src.utils.logger import get_logger


logger = get_logger("content_normalizer")


class ContentNormalizer:
    """Normalizes extracted text content"""

    def __init__(self):
        """Initialize content normalizer"""
        # Common hyphenation patterns
        self.hyphen_patterns = [
            (r'(\w+)-\s*\n\s*(\w+)', r'\1\2'),  # word- \n word → wordword
            (r'(\w+)-\s+(\w+)', r'\1\2'),  # word- word → wordword
        ]

        # Number format standardization
        self.number_patterns = [
            (r'Rule\s*\.\s*(\d+)', r'Rule \1'),  # Rule.5 → Rule 5
            (r'Rule\s*-\s*(\d+)', r'Rule \1'),  # Rule-5 → Rule 5
            (r'Sub-rule\s*\.\s*(\d+)', r'Sub-rule \1'),
            (r'Clause\s*\.\s*(\w+)', r'Clause \1'),
        ]

        # Special character normalization
        self.char_replacements = {
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'",
            '–': '-',
            '—': '-',
            '…': '...',
        }

    def normalize(self, text_lines: List[TextLine]) -> List[TextLine]:
        """
        Normalize text content

        Args:
            text_lines: List of text lines

        Returns:
            Normalized text lines
        """
        logger.info(f"Normalizing {len(text_lines)} text lines")

        normalized_lines = []

        for i, line in enumerate(text_lines):
            # Skip empty lines
            if not line.content.strip():
                continue

            content = line.content

            # Reconstruct broken words at line boundaries
            if i < len(text_lines) - 1 and content.endswith('-'):
                next_line = text_lines[i + 1]
                if self._is_word_continuation(content, next_line.content):
                    # Merge with next line
                    content = content[:-1] + next_line.content.lstrip()
                    # Skip next line in processing
                    continue

            # Standardize numbering
            content = self._standardize_numbering(content)

            # Normalize special characters
            content = self._normalize_special_chars(content)

            # Fix common OCR errors
            content = self._fix_ocr_errors(content)

            # Create normalized line
            normalized_line = TextLine(
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

            normalized_lines.append(normalized_line)

        logger.info(f"Normalized to {len(normalized_lines)} lines")
        return normalized_lines

    def _is_word_continuation(self, current: str, next_text: str) -> bool:
        """Check if next line continues a hyphenated word"""
        # Get the word fragment before hyphen
        last_word = current.split()[-1] if current.split() else ""

        # Get first word of next line
        first_word = next_text.split()[0] if next_text.split() else ""

        # If next line starts with lowercase and no punctuation, likely continuation
        if first_word and first_word[0].islower() and not current[-2].isspace():
            return True

        return False

    def _standardize_numbering(self, text: str) -> str:
        """Standardize numbering formats"""
        for pattern, replacement in self.number_patterns:
            text = re.sub(pattern, replacement, text)
        return text

    def _normalize_special_chars(self, text: str) -> str:
        """Normalize special characters"""
        for old_char, new_char in self.char_replacements.items():
            text = text.replace(old_char, new_char)
        return text

    def _fix_ocr_errors(self, text: str) -> str:
        """Fix common OCR errors"""
        # Common OCR mistakes
        ocr_fixes = {
            r'\bl\b': 'I',  # lowercase l → uppercase I in context
            r'\bO\b(?=\d)': '0',  # O → 0 before digits
            r'(?<=\d)O\b': '0',  # O → 0 after digits
        }

        for pattern, replacement in ocr_fixes.items():
            text = re.sub(pattern, replacement, text)

        return text

    def merge_broken_paragraphs(self, text_lines: List[TextLine]) -> List[TextLine]:
        """Merge lines that are part of same paragraph"""
        if not text_lines:
            return []

        merged_lines = []
        current_paragraph = []
        current_indent = text_lines[0].indentation if text_lines else 0

        for i, line in enumerate(text_lines):
            # Check if this line starts a new paragraph
            is_new_paragraph = (
                # Significant indent change
                abs(line.indentation - current_indent) > 10 or
                # Starts with capital and previous ends with period
                (line.content[0].isupper() if line.content else False) and
                (current_paragraph and current_paragraph[-1].content.endswith('.')) or
                # Number/bullet point
                bool(re.match(r'^[\d\(\)\[\]]+[\.\)]\s+', line.content)) or
                # Header-like (larger font)
                (i > 0 and line.font_size > text_lines[i-1].font_size + 1)
            )

            if is_new_paragraph and current_paragraph:
                # Merge current paragraph
                merged_lines.append(self._merge_lines(current_paragraph))
                current_paragraph = [line]
                current_indent = line.indentation
            else:
                current_paragraph.append(line)

        # Merge remaining paragraph
        if current_paragraph:
            merged_lines.append(self._merge_lines(current_paragraph))

        return merged_lines

    def _merge_lines(self, lines: List[TextLine]) -> TextLine:
        """Merge multiple lines into one"""
        if not lines:
            return None

        merged_content = ' '.join(line.content for line in lines)

        # Use properties from first line
        first_line = lines[0]

        return TextLine(
            content=merged_content,
            page_number=first_line.page_number,
            x=first_line.x,
            y=first_line.y,
            font_size=first_line.font_size,
            font_name=first_line.font_name,
            line_height=first_line.line_height,
            indentation=first_line.indentation,
            is_bold=first_line.is_bold,
            is_italic=first_line.is_italic
        )

"""
Government Order (GO) reconstruction
"""
import re
import hashlib
from typing import List, Optional
from datetime import datetime
from src.models.document import TextLine, GovernmentOrder
from src.modules.module2_reconstructor.gemini_client import GeminiClient
from src.utils.logger import get_logger
from src.utils.config_loader import get_config


logger = get_logger("go_reconstructor")


class GOReconstructor:
    """Reconstructs complete Government Orders from fragmented text"""

    def __init__(self):
        """Initialize GO reconstructor"""
        self.config = get_config()
        self.gemini = GeminiClient()

        # Get GO pattern from config
        self.go_pattern = self.config.get(
            'reconstruction.go_pattern',
            r'G\.O\.Ms\.No\.\s*\d+'
        )

    def reconstruct_gos(self, text_lines: List[TextLine]) -> List[GovernmentOrder]:
        """
        Reconstruct complete Government Orders from text lines

        Args:
            text_lines: List of text lines

        Returns:
            List of complete GOs
        """
        logger.info(f"Reconstructing GOs from {len(text_lines)} text lines")

        gos = []
        current_go = None
        i = 0

        while i < len(text_lines):
            line = text_lines[i]

            # Check if line starts a new GO
            if self._is_go_start(line):
                # Save previous GO if exists
                if current_go and current_go.content.strip():
                    gos.append(current_go)

                # Start new GO
                go_id = self._extract_go_id(line.content)
                go_date = self._extract_go_date(line.content, text_lines[i:i+5])

                current_go = GovernmentOrder(
                    go_id=go_id or f"GO_{len(gos)+1}",
                    date=go_date,
                    content=line.content,
                    start_page=line.page_number,
                    end_page=line.page_number,
                    header_hash=self._generate_header_hash(line.content)
                )

                logger.debug(f"Started GO {current_go.go_id} on page {line.page_number}")

            elif current_go is not None:
                # Check if this line belongs to current GO
                if not self._is_go_start(line):
                    current_go.content += "\n" + line.content
                    current_go.end_page = line.page_number
                else:
                    # New GO found, save current and restart
                    gos.append(current_go)

                    go_id = self._extract_go_id(line.content)
                    go_date = self._extract_go_date(line.content, text_lines[i:i+5])

                    current_go = GovernmentOrder(
                        go_id=go_id or f"GO_{len(gos)+1}",
                        date=go_date,
                        content=line.content,
                        start_page=line.page_number,
                        end_page=line.page_number,
                        header_hash=self._generate_header_hash(line.content)
                    )

            i += 1

        # Save last GO
        if current_go and current_go.content.strip():
            gos.append(current_go)

        logger.info(f"Reconstructed {len(gos)} GOs")
        return gos

    def _is_go_start(self, line: TextLine) -> bool:
        """Check if line starts a new GO"""
        return bool(re.search(self.go_pattern, line.content, re.IGNORECASE))

    def _extract_go_id(self, content: str) -> Optional[str]:
        """Extract GO ID from content"""
        match = re.search(r'G\.O\.Ms\.No\.\s*(\d+)', content, re.IGNORECASE)
        if match:
            return f"G.O.Ms.No.{match.group(1)}"
        return None

    def _extract_go_date(
        self,
        content: str,
        context_lines: List[TextLine]
    ) -> Optional[datetime]:
        """Extract GO date from content"""
        # Common date patterns
        date_patterns = [
            r'dt[:\.]?\s*(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})',
            r'dated?\s*[:\.]?\s*(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})',
            r'(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})',
        ]

        # Search in content
        for pattern in date_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                parsed_date = self._parse_date(date_str)
                if parsed_date:
                    return parsed_date

        # Search in context lines
        context_text = '\n'.join(line.content for line in context_lines)
        for pattern in date_patterns:
            match = re.search(pattern, context_text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                parsed_date = self._parse_date(date_str)
                if parsed_date:
                    return parsed_date

        return None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime"""
        # Get date formats from config
        date_formats = self.config.get('extraction.date_formats', [
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%d.%m.%Y'
        ])

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def _generate_header_hash(self, content: str) -> str:
        """Generate unique hash for GO header"""
        # Use first 200 characters for fingerprint
        fingerprint = content[:200].strip()
        return hashlib.md5(fingerprint.encode()).hexdigest()

    def extract_go_metadata(self, go: GovernmentOrder) -> GovernmentOrder:
        """
        Extract additional metadata from GO content

        Args:
            go: Government Order

        Returns:
            GO with enhanced metadata
        """
        content = go.content

        # Extract department
        dept_patterns = [
            r'(?:Department|Dept\.?)\s*[:\-]?\s*([^\n]+)',
            r'([A-Z][A-Za-z\s&]+(?:Department|Dept))',
        ]

        for pattern in dept_patterns:
            match = re.search(pattern, content[:500])
            if match:
                go.department = match.group(1).strip()
                break

        # Extract file number
        file_patterns = [
            r'F\.?\s*No\.?\s*[:\-]?\s*([\d/\-A-Z]+)',
            r'File\s*No\.?\s*[:\-]?\s*([\d/\-A-Z]+)',
        ]

        for pattern in file_patterns:
            match = re.search(pattern, content[:500])
            if match:
                go.file_number = match.group(1).strip()
                break

        # Extract effective date (if different from issuance date)
        effective_patterns = [
            r'effective\s*from\s*[:\-]?\s*(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})',
            r'w\.?e\.?f\.?\s*[:\-]?\s*(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})',
        ]

        for pattern in effective_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                effective_date = self._parse_date(date_str)
                if effective_date:
                    go.effective_date = effective_date
                    break

        return go

    def handle_multi_page_gos(
        self,
        gos: List[GovernmentOrder]
    ) -> List[GovernmentOrder]:
        """
        Handle GOs that span multiple pages

        Args:
            gos: List of GOs

        Returns:
            GOs with proper multi-page handling
        """
        # GOs are already reconstructed across pages
        # This method can add additional validation

        for go in gos:
            if go.end_page > go.start_page:
                logger.debug(
                    f"GO {go.go_id} spans {go.end_page - go.start_page + 1} pages"
                )

        return gos

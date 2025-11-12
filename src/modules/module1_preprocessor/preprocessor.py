"""
Module 1: Document Preprocessor
Main orchestrator for PDF preprocessing
"""
from typing import Tuple, List
from pathlib import Path

from src.models.document import TextLine, PageMetadata, DocumentFingerprint
from src.modules.module1_preprocessor.pdf_extractor import PDFExtractor
from src.modules.module1_preprocessor.content_normalizer import ContentNormalizer
from src.modules.module1_preprocessor.noise_filter import NoiseFilter
from src.utils.logger import get_logger
from src.utils.config_loader import get_config


logger = get_logger("preprocessor")


class DocumentPreprocessor:
    """
    Module 1: Document Preprocessor
    Transforms raw PDF into structured, normalized content
    """

    def __init__(self):
        """Initialize document preprocessor"""
        self.config = get_config()
        self.pdf_extractor = PDFExtractor()
        self.content_normalizer = ContentNormalizer()

        # Get noise filter threshold from config
        threshold = self.config.get('preprocessing.header_footer_threshold', 0.9)
        self.noise_filter = NoiseFilter(repetition_threshold=threshold)

    def process(self, pdf_path: str) -> Tuple[DocumentFingerprint, List[PageMetadata], List[TextLine]]:
        """
        Process PDF document through all preprocessing steps

        Args:
            pdf_path: Path to PDF file

        Returns:
            Tuple of (fingerprint, page_metadata, text_lines)
        """
        logger.info(f"Starting preprocessing for: {pdf_path}")

        # Validate file exists
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Step 1: Extract text with metadata
        logger.info("Step 1: Extracting text from PDF...")
        pages, text_lines = self.pdf_extractor.extract(pdf_path)

        # Step 2: Normalize content
        logger.info("Step 2: Normalizing content...")
        normalized_lines = self.content_normalizer.normalize(text_lines)

        # Step 3: Filter noise
        logger.info("Step 3: Filtering noise...")
        filtered_lines = self.noise_filter.filter(normalized_lines, pages)

        # Step 4: Remove scan artifacts
        logger.info("Step 4: Removing scan artifacts...")
        clean_lines = self.noise_filter.remove_scan_artifacts(filtered_lines)

        # Step 5: Generate document fingerprint
        logger.info("Step 5: Generating document fingerprint...")
        fingerprint = self.pdf_extractor.generate_fingerprint(pages, clean_lines)

        logger.info(f"Preprocessing complete:")
        logger.info(f"  - Pages: {len(pages)}")
        logger.info(f"  - Text lines: {len(clean_lines)}")
        logger.info(f"  - Document type: {fingerprint.document_type.value}")

        return fingerprint, pages, clean_lines


def main():
    """Test the preprocessor"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python preprocessor.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    preprocessor = DocumentPreprocessor()
    fingerprint, pages, text_lines = preprocessor.process(pdf_path)

    print(f"\nDocument Fingerprint:")
    print(f"  Type: {fingerprint.document_type.value}")
    print(f"  Pages: {fingerprint.total_pages}")
    print(f"  Hash: {fingerprint.structure_hash}")
    print(f"  First 100 chars: {fingerprint.first_100_chars[:50]}...")

    print(f"\nSample Text Lines (first 10):")
    for i, line in enumerate(text_lines[:10], 1):
        print(f"  {i}. [Page {line.page_number}] {line.content[:80]}...")


if __name__ == "__main__":
    main()

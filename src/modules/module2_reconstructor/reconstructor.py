"""
Module 2: Logical Unit Reconstructor
Main orchestrator for rebuilding logical units
"""
from typing import List, Tuple

from src.models.document import TextLine, Rule, GovernmentOrder
from src.modules.module2_reconstructor.rule_reconstructor import RuleReconstructor
from src.modules.module2_reconstructor.go_reconstructor import GOReconstructor
from src.utils.logger import get_logger


logger = get_logger("reconstructor")


class LogicalUnitReconstructor:
    """
    Module 2: Logical Unit Reconstructor
    Rebuilds multi-page rules and GOs into coherent logical units
    """

    def __init__(self):
        """Initialize logical unit reconstructor"""
        self.rule_reconstructor = RuleReconstructor()
        self.go_reconstructor = GOReconstructor()

    def reconstruct(
        self,
        text_lines: List[TextLine]
    ) -> Tuple[List[Rule], List[GovernmentOrder]]:
        """
        Reconstruct logical units from text lines

        Args:
            text_lines: Preprocessed text lines

        Returns:
            Tuple of (rules, government_orders)
        """
        logger.info(f"Starting logical unit reconstruction from {len(text_lines)} text lines")

        # Step 1: Reconstruct rules
        logger.info("Step 1: Reconstructing rules...")
        rules = self.rule_reconstructor.reconstruct_rules(text_lines)

        # Step 2: Handle rule page continuations
        logger.info("Step 2: Handling rule page continuations...")
        rules = self.rule_reconstructor.handle_page_continuations(rules, text_lines)

        # Step 3: Build rule hierarchy
        logger.info("Step 3: Building rule hierarchy...")
        rules = self.rule_reconstructor.build_rule_hierarchy(rules)

        # Step 4: Reconstruct GOs
        logger.info("Step 4: Reconstructing Government Orders...")
        gos = self.go_reconstructor.reconstruct_gos(text_lines)

        # Step 5: Extract GO metadata
        logger.info("Step 5: Extracting GO metadata...")
        gos = [self.go_reconstructor.extract_go_metadata(go) for go in gos]

        # Step 6: Handle multi-page GOs
        logger.info("Step 6: Handling multi-page GOs...")
        gos = self.go_reconstructor.handle_multi_page_gos(gos)

        logger.info(f"Reconstruction complete:")
        logger.info(f"  - Rules: {len(rules)}")
        logger.info(f"  - Government Orders: {len(gos)}")

        return rules, gos

    def resolve_orphaned_content(
        self,
        text_lines: List[TextLine],
        rules: List[Rule],
        gos: List[GovernmentOrder]
    ) -> Tuple[List[Rule], List[GovernmentOrder]]:
        """
        Resolve orphaned content that wasn't assigned to any logical unit

        Args:
            text_lines: Original text lines
            rules: Reconstructed rules
            gos: Reconstructed GOs

        Returns:
            Updated (rules, gos) with orphaned content resolved
        """
        logger.info("Resolving orphaned content...")

        # Identify assigned lines
        assigned_pages = set()

        for rule in rules:
            for page in range(rule.start_page, rule.end_page + 1):
                assigned_pages.add(page)

        for go in gos:
            for page in range(go.start_page, go.end_page + 1):
                assigned_pages.add(page)

        # Find orphaned pages
        all_pages = set(line.page_number for line in text_lines)
        orphaned_pages = all_pages - assigned_pages

        if orphaned_pages:
            logger.warning(f"Found {len(orphaned_pages)} orphaned pages: {sorted(orphaned_pages)}")

            # TODO: Implement orphaned content assignment logic
            # Using semantic similarity, font consistency, etc.

        return rules, gos


def main():
    """Test the reconstructor"""
    import sys
    from src.modules.module1_preprocessor.preprocessor import DocumentPreprocessor

    if len(sys.argv) < 2:
        print("Usage: python reconstructor.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # Preprocess
    preprocessor = DocumentPreprocessor()
    fingerprint, pages, text_lines = preprocessor.process(pdf_path)

    # Reconstruct
    reconstructor = LogicalUnitReconstructor()
    rules, gos = reconstructor.reconstruct(text_lines)

    print(f"\nReconstructed Logical Units:")
    print(f"  Rules: {len(rules)}")
    for i, rule in enumerate(rules[:5], 1):
        print(f"    {i}. {rule.display_number} (Pages {rule.start_page}-{rule.end_page})")

    print(f"\n  Government Orders: {len(gos)}")
    for i, go in enumerate(gos[:5], 1):
        date_str = go.date.strftime('%Y-%m-%d') if go.date else 'Unknown'
        print(f"    {i}. {go.go_id} ({date_str}) (Pages {go.start_page}-{go.end_page})")


if __name__ == "__main__":
    main()

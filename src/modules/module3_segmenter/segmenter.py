"""
Module 3: Document Segmenter
Separates document into base rulebook and amendment sections
"""
from typing import List, Tuple, Dict, Any
import re

from src.models.document import Rule, GovernmentOrder
from src.modules.module2_reconstructor.gemini_client import GeminiClient
from src.utils.logger import get_logger
from src.utils.config_loader import get_config


logger = get_logger("segmenter")


class DocumentSegmenter:
    """
    Module 3: Document Segmenter
    Separates document into base rulebook and amendment sections
    """

    def __init__(self):
        """Initialize document segmenter"""
        self.config = get_config()
        self.gemini = GeminiClient()

        # Get transition keywords from config
        self.transition_keywords = self.config.get(
            'segmentation.transition_keywords',
            ['G.O.Ms.No', 'ABSTRACT', 'Government Order']
        )

        self.amendment_verbs = self.config.get(
            'segmentation.amendment_verbs',
            ['substitute', 'insert', 'omit', 'delete', 'add', 'replace']
        )

    def segment(
        self,
        rules: List[Rule],
        gos: List[GovernmentOrder]
    ) -> Tuple[List[Rule], List[GovernmentOrder], Dict[str, Any]]:
        """
        Segment document into base rulebook and amendments

        Args:
            rules: All reconstructed rules
            gos: All reconstructed GOs

        Returns:
            Tuple of (base_rules, amendment_gos, metadata)
        """
        logger.info(f"Segmenting document: {len(rules)} rules, {len(gos)} GOs")

        # Determine document structure
        structure = self._analyze_document_structure(rules, gos)

        if structure['type'] == 'MIXED':
            # Document has interspersed rules and GOs
            base_rules, amendment_gos = self._segment_mixed_document(rules, gos)

        elif structure['type'] == 'SEQUENTIAL':
            # Rules first, then GOs
            base_rules, amendment_gos = self._segment_sequential_document(rules, gos)

        else:
            # Simple case: all rules or all GOs
            base_rules = rules
            amendment_gos = gos

        # Sort GOs chronologically
        amendment_gos = self._sort_gos_chronologically(amendment_gos)

        # Validate segmentation
        validation_result = self._validate_segmentation(base_rules, amendment_gos)

        logger.info(f"Segmentation complete:")
        logger.info(f"  - Base rules: {len(base_rules)}")
        logger.info(f"  - Amendment GOs: {len(amendment_gos)}")

        metadata = {
            'structure': structure,
            'validation': validation_result
        }

        return base_rules, amendment_gos, metadata

    def _analyze_document_structure(
        self,
        rules: List[Rule],
        gos: List[GovernmentOrder]
    ) -> Dict[str, Any]:
        """Analyze document structure"""
        if not rules and not gos:
            return {'type': 'EMPTY'}

        if not rules:
            return {'type': 'AMENDMENTS_ONLY'}

        if not gos:
            return {'type': 'RULEBOOK_ONLY'}

        # Check if interspersed
        rule_pages = set()
        for rule in rules:
            rule_pages.update(range(rule.start_page, rule.end_page + 1))

        go_pages = set()
        for go in gos:
            go_pages.update(range(go.start_page, go.end_page + 1))

        # Check overlap
        overlap = rule_pages & go_pages
        if overlap:
            return {
                'type': 'MIXED',
                'overlap_pages': len(overlap)
            }

        # Check if sequential
        max_rule_page = max(rule.end_page for rule in rules) if rules else 0
        min_go_page = min(go.start_page for go in gos) if gos else float('inf')

        if max_rule_page < min_go_page:
            return {
                'type': 'SEQUENTIAL',
                'transition_page': max_rule_page
            }

        return {'type': 'UNKNOWN'}

    def _segment_mixed_document(
        self,
        rules: List[Rule],
        gos: List[GovernmentOrder]
    ) -> Tuple[List[Rule], List[GovernmentOrder]]:
        """Segment document with interspersed content"""
        logger.info("Segmenting mixed document...")

        # Use heuristics to classify
        base_rules = []
        amendment_gos = []

        for rule in rules:
            # Check if rule is actually part of amendment section
            if self._is_amendment_section(rule.content):
                logger.debug(f"Rule {rule.display_number} classified as amendment")
                # Convert to GO or skip
                continue
            else:
                base_rules.append(rule)

        # All GOs are amendments by default
        amendment_gos = gos

        return base_rules, amendment_gos

    def _segment_sequential_document(
        self,
        rules: List[Rule],
        gos: List[GovernmentOrder]
    ) -> Tuple[List[Rule], List[GovernmentOrder]]:
        """Segment document with sequential structure"""
        logger.info("Segmenting sequential document...")

        # Simple case: rules are base, GOs are amendments
        return rules, gos

    def _is_amendment_section(self, content: str) -> bool:
        """Check if content belongs to amendment section"""
        content_lower = content.lower()

        # Check for amendment verbs
        amendment_verb_count = sum(
            1 for verb in self.amendment_verbs
            if verb in content_lower
        )

        # Check for GO patterns
        go_pattern_matches = len(re.findall(
            r'g\.o\.ms\.no',
            content_lower
        ))

        # Heuristic: if >2 amendment verbs or >1 GO reference, it's amendment section
        return amendment_verb_count >= 2 or go_pattern_matches >= 1

    def _sort_gos_chronologically(
        self,
        gos: List[GovernmentOrder]
    ) -> List[GovernmentOrder]:
        """Sort GOs by date"""
        # Separate GOs with and without dates
        dated_gos = [go for go in gos if go.date is not None]
        undated_gos = [go for go in gos if go.date is None]

        # Sort dated GOs
        dated_gos.sort(key=lambda go: go.date)

        # Combine: dated first, then undated (in original order)
        return dated_gos + undated_gos

    def _validate_segmentation(
        self,
        base_rules: List[Rule],
        amendment_gos: List[GovernmentOrder]
    ) -> Dict[str, Any]:
        """Validate segmentation results"""
        validation = {
            'base_rules_count': len(base_rules),
            'amendment_gos_count': len(amendment_gos),
            'warnings': [],
            'errors': []
        }

        # Check for minimum rules
        if len(base_rules) < 5:
            validation['warnings'].append(
                f"Base rulebook has only {len(base_rules)} rules (expected ≥5)"
            )

        # Check for dated GOs
        dated_gos = [go for go in amendment_gos if go.date is not None]
        if dated_gos and len(dated_gos) < len(amendment_gos) * 0.8:
            validation['warnings'].append(
                f"Only {len(dated_gos)}/{len(amendment_gos)} GOs have dates"
            )

        # Check for GO metadata
        gos_with_metadata = [
            go for go in amendment_gos
            if go.department or go.file_number
        ]
        if gos_with_metadata:
            logger.info(f"{len(gos_with_metadata)} GOs have metadata")

        validation['passed'] = len(validation['errors']) == 0

        return validation

    def detect_transition_point(self, rules: List[Rule], gos: List[GovernmentOrder]) -> int:
        """
        Detect the page where document transitions from rulebook to amendments

        Args:
            rules: All rules
            gos: All GOs

        Returns:
            Page number of transition point
        """
        if not gos:
            return float('inf')

        # Find first GO
        first_go = min(gos, key=lambda go: go.start_page)

        # Find last rule before first GO
        rules_before_go = [
            rule for rule in rules
            if rule.end_page < first_go.start_page
        ]

        if rules_before_go:
            last_rule = max(rules_before_go, key=lambda r: r.end_page)
            return last_rule.end_page

        return first_go.start_page


def main():
    """Test the segmenter"""
    import sys
    from src.modules.module1_preprocessor.preprocessor import DocumentPreprocessor
    from src.modules.module2_reconstructor.reconstructor import LogicalUnitReconstructor

    if len(sys.argv) < 2:
        print("Usage: python segmenter.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # Preprocess
    preprocessor = DocumentPreprocessor()
    fingerprint, pages, text_lines = preprocessor.process(pdf_path)

    # Reconstruct
    reconstructor = LogicalUnitReconstructor()
    rules, gos = reconstructor.reconstruct(text_lines)

    # Segment
    segmenter = DocumentSegmenter()
    base_rules, amendment_gos, metadata = segmenter.segment(rules, gos)

    print(f"\nSegmentation Results:")
    print(f"  Structure: {metadata['structure']['type']}")
    print(f"  Base Rules: {len(base_rules)}")
    print(f"  Amendment GOs: {len(amendment_gos)}")

    if metadata['validation']['warnings']:
        print(f"\n  Warnings:")
        for warning in metadata['validation']['warnings']:
            print(f"    - {warning}")


if __name__ == "__main__":
    main()

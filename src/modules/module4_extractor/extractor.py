"""
Module 4: Amendment Extractor
Converts GO text into structured machine-actionable amendments
"""
from typing import List, Dict, Any
from datetime import datetime

from src.models.document import GovernmentOrder, Amendment, AmendmentAction
from src.modules.module4_extractor.adk_agent import AmendmentExtractionAgent
from src.utils.logger import get_logger
from src.utils.config_loader import get_config


logger = get_logger("extractor")


class AmendmentExtractor:
    """
    Module 4: Amendment Extractor
    Converts GO text into structured machine-actionable amendment instructions
    """

    def __init__(self):
        """Initialize amendment extractor"""
        self.config = get_config()
        self.agent = AmendmentExtractionAgent()

    def extract(
        self,
        gos: List[GovernmentOrder]
    ) -> List[Amendment]:
        """
        Extract structured amendments from all GOs

        Args:
            gos: List of Government Orders

        Returns:
            List of structured amendments
        """
        logger.info(f"Extracting amendments from {len(gos)} GOs")

        all_amendments = []

        for go in gos:
            # Extract amendments from this GO
            go_amendments = self._extract_from_go(go)
            all_amendments.extend(go_amendments)

        # Sort chronologically
        all_amendments = self._sort_chronologically(all_amendments)

        logger.info(f"Extracted {len(all_amendments)} total amendments")

        # Log flagged amendments
        flagged = [a for a in all_amendments if a.flagged]
        if flagged:
            logger.warning(f"{len(flagged)} amendments flagged for review")

        return all_amendments

    def _extract_from_go(self, go: GovernmentOrder) -> List[Amendment]:
        """Extract amendments from a single GO"""
        logger.debug(f"Processing {go.go_id}")

        # Use ADK agent to extract
        go_date_str = go.date.isoformat() if go.date else None
        raw_amendments = self.agent.extract_amendments_from_go(
            go.content,
            go.go_id,
            go_date_str
        )

        # Convert to Amendment objects
        amendments = []
        for raw_amend in raw_amendments:
            amendment = self._create_amendment_object(raw_amend, go)

            # Validate
            validated = self.agent.validate_amendment(raw_amend)
            amendment.flagged = validated.get('flagged', False)
            amendment.flag_reason = ', '.join(validated.get('flag_reasons', []))

            amendments.append(amendment)

        return amendments

    def _create_amendment_object(
        self,
        raw_data: Dict[str, Any],
        go: GovernmentOrder
    ) -> Amendment:
        """Create Amendment object from raw data"""
        # Parse action
        action_str = raw_data.get('action', 'SUBSTITUTE').upper()
        try:
            action = AmendmentAction[action_str]
        except KeyError:
            logger.warning(f"Unknown action type: {action_str}, defaulting to SUBSTITUTE")
            action = AmendmentAction.SUBSTITUTE

        # Create amendment
        amendment = Amendment(
            go_id=go.go_id,
            go_uuid=go.uuid,
            date=go.date,
            effective_date=go.effective_date,
            action=action,
            target_path=raw_data.get('target_path', []),
            old_text=raw_data.get('old_text'),
            new_text=raw_data.get('new_text'),
            position=raw_data.get('position'),
            confidence=raw_data.get('confidence', 1.0),
            context=raw_data.get('context')
        )

        return amendment

    def _sort_chronologically(self, amendments: List[Amendment]) -> List[Amendment]:
        """Sort amendments by date"""
        # Separate dated and undated
        dated = [a for a in amendments if a.date is not None]
        undated = [a for a in amendments if a.date is None]

        # Sort dated
        dated.sort(key=lambda a: a.date)

        # Combine
        return dated + undated

    def resolve_ambiguous_references(
        self,
        amendments: List[Amendment],
        available_rules: List[str]
    ) -> List[Amendment]:
        """
        Resolve ambiguous target references

        Args:
            amendments: List of amendments
            available_rules: List of available rule numbers

        Returns:
            Amendments with resolved references
        """
        logger.info("Resolving ambiguous references...")

        resolved = []

        for amendment in amendments:
            # Check if target path is incomplete
            if not amendment.target_path or len(amendment.target_path) == 0:
                # Try to resolve using context
                if amendment.context:
                    # Extract reference from context
                    # e.g., "in the said rule" → need to look at context

                    resolved_path = self.agent.resolve_ambiguous_target(
                        "unknown",
                        amendment.context,
                        available_rules
                    )

                    if resolved_path:
                        amendment.target_path = resolved_path
                        logger.debug(f"Resolved ambiguous reference to {resolved_path}")
                    else:
                        amendment.flagged = True
                        amendment.flag_reason = "Could not resolve ambiguous target"

            resolved.append(amendment)

        return resolved

    def detect_conflicts(self, amendments: List[Amendment]) -> List[Dict[str, Any]]:
        """
        Detect conflicts between amendments

        Args:
            amendments: List of amendments

        Returns:
            List of detected conflicts
        """
        logger.info("Detecting conflicts...")

        conflicts = []

        # Group amendments by target
        target_groups = {}
        for amendment in amendments:
            target_key = '-'.join(amendment.target_path)
            if target_key not in target_groups:
                target_groups[target_key] = []
            target_groups[target_key].append(amendment)

        # Check for conflicts within each group
        for target, group in target_groups.items():
            if len(group) > 1:
                # Check for same-date modifications
                date_groups = {}
                for amend in group:
                    date_key = amend.date.isoformat() if amend.date else 'undated'
                    if date_key not in date_groups:
                        date_groups[date_key] = []
                    date_groups[date_key].append(amend)

                for date_key, date_group in date_groups.items():
                    if len(date_group) > 1:
                        conflict = {
                            'type': 'SAME_DATE_MODIFICATION',
                            'target': target,
                            'date': date_key,
                            'amendments': [a.go_id for a in date_group],
                            'count': len(date_group)
                        }
                        conflicts.append(conflict)
                        logger.warning(f"Conflict detected: {conflict['type']} on {target}")

        logger.info(f"Detected {len(conflicts)} conflicts")
        return conflicts


def main():
    """Test the extractor"""
    import sys
    from src.modules.module1_preprocessor.preprocessor import DocumentPreprocessor
    from src.modules.module2_reconstructor.reconstructor import LogicalUnitReconstructor
    from src.modules.module3_segmenter.segmenter import DocumentSegmenter

    if len(sys.argv) < 2:
        print("Usage: python extractor.py <pdf_path>")
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

    # Extract amendments
    extractor = AmendmentExtractor()
    amendments = extractor.extract(amendment_gos)

    print(f"\nExtraction Results:")
    print(f"  Total Amendments: {len(amendments)}")

    # Show sample amendments
    print(f"\n  Sample Amendments:")
    for i, amend in enumerate(amendments[:3], 1):
        print(f"    {i}. {amend.action.value} on {'-'.join(amend.target_path)}")
        print(f"       From GO: {amend.go_id}")
        print(f"       Confidence: {amend.confidence:.2f}")
        if amend.flagged:
            print(f"       ⚠ FLAGGED: {amend.flag_reason}")

    # Detect conflicts
    conflicts = extractor.detect_conflicts(amendments)
    if conflicts:
        print(f"\n  Detected {len(conflicts)} conflicts")


if __name__ == "__main__":
    main()

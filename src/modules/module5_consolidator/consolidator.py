"""
Module 5: Rulebook Consolidation Engine
Dynamically applies amendments to base rulebook
"""
from typing import List, Dict, Any
import uuid as uuid_lib
from copy import deepcopy

from src.models.document import Rule, Amendment, AmendmentAction
from src.modules.module5_consolidator.rule_tree import RuleTree, RuleNode
from src.utils.logger import get_logger
from src.utils.config_loader import get_config


logger = get_logger("consolidator")


class RulebookConsolidator:
    """
    Module 5: Rulebook Consolidation Engine
    Dynamically applies amendments to base rulebook while handling structural evolution
    """

    def __init__(self):
        """Initialize rulebook consolidator"""
        self.config = get_config()
        self.tree = RuleTree()
        self.snapshots: List[Dict[str, Any]] = []
        self.conflicts: List[Dict[str, Any]] = []

    def consolidate(
        self,
        base_rules: List[Rule],
        amendments: List[Amendment]
    ) -> RuleTree:
        """
        Consolidate rulebook by applying all amendments

        Args:
            base_rules: Base rules
            amendments: Chronologically sorted amendments

        Returns:
            Consolidated RuleTree
        """
        logger.info(f"Consolidating rulebook: {len(base_rules)} base rules, {len(amendments)} amendments")

        # Step 1: Build initial tree
        logger.info("Step 1: Building initial rule tree...")
        self._build_initial_tree(base_rules)

        # Step 2: Apply amendments chronologically
        logger.info("Step 2: Applying amendments chronologically...")
        self._apply_amendments(amendments)

        # Step 3: Validate final state
        logger.info("Step 3: Validating final state...")
        self._validate_final_state()

        logger.info(f"Consolidation complete:")
        logger.info(f"  - Final rules: {len(self.tree.get_all_rules())}")
        logger.info(f"  - Snapshots taken: {len(self.snapshots)}")
        logger.info(f"  - Conflicts detected: {len(self.conflicts)}")

        return self.tree

    def _build_initial_tree(self, base_rules: List[Rule]):
        """Build initial rule tree from base rules"""
        for rule in base_rules:
            self.tree.add_rule(rule)

    def _apply_amendments(self, amendments: List[Amendment]):
        """Apply all amendments chronologically"""
        for i, amendment in enumerate(amendments):
            logger.debug(f"Applying amendment {i+1}/{len(amendments)}: {amendment.go_id}")

            # Take snapshot before applying
            if i % 10 == 0:  # Snapshot every 10 amendments
                self._take_snapshot(f"Before amendment {i+1}")

            # Apply amendment
            try:
                success = self._apply_single_amendment(amendment)
                if not success:
                    logger.warning(f"Failed to apply amendment from {amendment.go_id}")
            except Exception as e:
                logger.error(f"Error applying amendment from {amendment.go_id}: {str(e)}")

    def _apply_single_amendment(self, amendment: Amendment) -> bool:
        """
        Apply a single amendment to the tree

        Args:
            amendment: Amendment to apply

        Returns:
            Success boolean
        """
        # Resolve target
        target_node = self.tree.find_by_path(amendment.target_path)

        if not target_node:
            logger.warning(f"Target not found for amendment: {amendment.target_path}")
            self.conflicts.append({
                'type': 'TARGET_NOT_FOUND',
                'amendment': amendment.go_id,
                'target_path': amendment.target_path
            })
            return False

        # Apply based on action type
        if amendment.action == AmendmentAction.SUBSTITUTE:
            return self._apply_substitute(amendment, target_node)

        elif amendment.action == AmendmentAction.OMIT:
            return self._apply_omit(amendment, target_node)

        elif amendment.action == AmendmentAction.INSERT:
            return self._apply_insert(amendment, target_node)

        elif amendment.action == AmendmentAction.RENUMBER:
            return self._apply_renumber(amendment, target_node)

        else:
            logger.warning(f"Unknown amendment action: {amendment.action}")
            return False

    def _apply_substitute(self, amendment: Amendment, target_node: RuleNode) -> bool:
        """Apply SUBSTITUTE amendment"""
        logger.debug(f"SUBSTITUTE on {target_node.display_number}")

        # Replace content
        old_content = target_node.content
        target_node.content = amendment.new_text or ""

        # Record in history
        target_node.amendment_history.append(amendment)

        logger.debug(f"Substituted content in {target_node.display_number}")
        return True

    def _apply_omit(self, amendment: Amendment, target_node: RuleNode) -> bool:
        """Apply OMIT amendment"""
        logger.debug(f"OMIT {target_node.display_number}")

        # Remove node and descendants
        success = self.tree.remove_node(target_node.uuid)

        if success:
            # Renumber siblings if needed
            if target_node.parent_uuid:
                self.tree.renumber_nodes(target_node.parent_uuid)

            logger.debug(f"Omitted {target_node.display_number}")

        return success

    def _apply_insert(self, amendment: Amendment, target_node: RuleNode) -> bool:
        """Apply INSERT amendment"""
        logger.debug(f"INSERT at {target_node.display_number}")

        # Create new node
        new_display_number = self._generate_insert_number(
            target_node.display_number,
            amendment.position
        )

        new_node = RuleNode(
            uuid=str(uuid_lib.uuid4()),
            display_number=new_display_number,
            content=amendment.new_text or "",
            level=target_node.level,
            parent_uuid=target_node.parent_uuid
        )

        # Record amendment in new node
        new_node.amendment_history.append(amendment)

        # Insert node
        position = amendment.position or "after"
        success = self.tree.insert_node(
            new_node,
            target_node.parent_uuid or self.tree.root.uuid,
            position=position,
            reference_display_number=target_node.display_number
        )

        if success:
            logger.debug(f"Inserted new rule {new_display_number}")

            # Renumber subsequent rules if needed
            if target_node.parent_uuid:
                self.tree.renumber_nodes(target_node.parent_uuid)

        return success

    def _apply_renumber(self, amendment: Amendment, target_node: RuleNode) -> bool:
        """Apply RENUMBER amendment"""
        logger.debug(f"RENUMBER {target_node.display_number}")

        # Extract new number from amendment
        new_number = amendment.new_text or ""

        # Update display number
        old_display = target_node.display_number

        # Remove old mapping
        if old_display in self.tree.display_map:
            del self.tree.display_map[old_display]

        # Update node
        target_node.display_number = new_number
        target_node.amendment_history.append(amendment)

        # Add new mapping
        self.tree.display_map[new_number] = target_node.uuid

        logger.debug(f"Renumbered {old_display} -> {new_number}")
        return True

    def _generate_insert_number(self, reference_number: str, position: str) -> str:
        """
        Generate numbering for inserted rules

        Args:
            reference_number: Reference rule number
            position: "before" or "after"

        Returns:
            New rule number
        """
        # Get numbering conventions from config
        conventions = self.config.get('consolidation.numbering_conventions', {
            'after_rule': ['A', 'B', 'C', 'D'],
            'after_clause': ['-1', '-2', '-3']
        })

        # Simple heuristic: append A, B, C, etc.
        # Check if reference already has letter suffix
        import re
        match = re.match(r'(\d+)([A-Z])?', reference_number)

        if match:
            base_num = match.group(1)
            suffix = match.group(2)

            if suffix:
                # Increment suffix
                next_suffix = chr(ord(suffix) + 1)
            else:
                # Add first suffix
                next_suffix = 'A'

            return f"{base_num}{next_suffix}"

        # Fallback
        return f"{reference_number}A"

    def _take_snapshot(self, label: str):
        """Take snapshot of current tree state"""
        snapshot = {
            'label': label,
            'total_rules': len(self.tree.get_all_rules()),
            'timestamp': label
        }
        self.snapshots.append(snapshot)
        logger.debug(f"Snapshot taken: {label}")

    def _validate_final_state(self):
        """Validate final consolidated state"""
        all_rules = self.tree.get_all_rules()

        # Check for numbering gaps
        rule_numbers = [node.display_number for node in all_rules if node.level == 0]
        logger.info(f"Final rule numbers: {sorted(rule_numbers, key=lambda x: (int(re.match(r'\\d+', x).group()) if re.match(r'\\d+', x) else 0))}")

        # Check for empty content
        empty_rules = [node for node in all_rules if not node.content.strip()]
        if empty_rules:
            logger.warning(f"Found {len(empty_rules)} rules with empty content")

    def get_consolidated_rules(self) -> List[Rule]:
        """
        Get consolidated rules as list

        Returns:
            List of Rule objects
        """
        all_nodes = self.tree.get_all_rules()

        rules = []
        for node in all_nodes:
            rule = Rule(
                uuid=node.uuid,
                display_number=node.display_number,
                content=node.content,
                level=node.level,
                parent_uuid=node.parent_uuid,
                amendment_history=node.amendment_history
            )
            rules.append(rule)

        return rules


def main():
    """Test the consolidator"""
    import sys
    from src.modules.module1_preprocessor.preprocessor import DocumentPreprocessor
    from src.modules.module2_reconstructor.reconstructor import LogicalUnitReconstructor
    from src.modules.module3_segmenter.segmenter import DocumentSegmenter
    from src.modules.module4_extractor.extractor import AmendmentExtractor

    if len(sys.argv) < 2:
        print("Usage: python consolidator.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # Full pipeline
    preprocessor = DocumentPreprocessor()
    fingerprint, pages, text_lines = preprocessor.process(pdf_path)

    reconstructor = LogicalUnitReconstructor()
    rules, gos = reconstructor.reconstruct(text_lines)

    segmenter = DocumentSegmenter()
    base_rules, amendment_gos, metadata = segmenter.segment(rules, gos)

    extractor = AmendmentExtractor()
    amendments = extractor.extract(amendment_gos)

    # Consolidate
    consolidator = RulebookConsolidator()
    tree = consolidator.consolidate(base_rules, amendments)

    print(f"\nConsolidation Results:")
    print(f"  Initial Rules: {len(base_rules)}")
    print(f"  Amendments Applied: {len(amendments)}")
    print(f"  Final Rules: {len(tree.get_all_rules())}")
    print(f"  Conflicts: {len(consolidator.conflicts)}")


if __name__ == "__main__":
    main()

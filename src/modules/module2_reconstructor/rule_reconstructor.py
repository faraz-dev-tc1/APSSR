"""
Rule reconstruction - rebuilds multi-page rules
"""
import re
from typing import List, Optional
from src.models.document import TextLine, Rule
from src.modules.module2_reconstructor.gemini_client import GeminiClient
from src.utils.logger import get_logger
from src.utils.config_loader import get_config


logger = get_logger("rule_reconstructor")


class RuleReconstructor:
    """Reconstructs complete rules from fragmented text"""

    def __init__(self):
        """Initialize rule reconstructor"""
        self.config = get_config()
        self.gemini = GeminiClient()

        # Get rule pattern from config
        self.rule_pattern = self.config.get(
            'reconstruction.rule_pattern',
            r'Rule\s+[0-9A-Z]+'
        )

        self.continuation_threshold = self.config.get(
            'reconstruction.continuation_threshold',
            0.15
        )

    def reconstruct_rules(self, text_lines: List[TextLine]) -> List[Rule]:
        """
        Reconstruct complete rules from text lines

        Args:
            text_lines: List of text lines

        Returns:
            List of complete rules
        """
        logger.info(f"Reconstructing rules from {len(text_lines)} text lines")

        rules = []
        current_rule = None
        i = 0

        while i < len(text_lines):
            line = text_lines[i]

            # Check if line starts a new rule
            if self._is_rule_start(line):
                # Save previous rule if exists
                if current_rule and current_rule.content.strip():
                    rules.append(current_rule)

                # Start new rule
                rule_number = self._extract_rule_number(line.content)
                current_rule = Rule(
                    display_number=rule_number or f"Rule_{len(rules)+1}",
                    content=line.content,
                    start_page=line.page_number,
                    end_page=line.page_number,
                    level=0
                )

                logger.debug(f"Started Rule {current_rule.display_number} on page {line.page_number}")

            elif current_rule is not None:
                # Add to current rule
                current_rule.content += "\n" + line.content
                current_rule.end_page = line.page_number

            i += 1

        # Save last rule
        if current_rule and current_rule.content.strip():
            rules.append(current_rule)

        logger.info(f"Reconstructed {len(rules)} rules")
        return rules

    def _is_rule_start(self, line: TextLine) -> bool:
        """Check if line starts a new rule"""
        # Pattern match
        if re.search(self.rule_pattern, line.content, re.IGNORECASE):
            # Additional heuristics
            # Larger font size
            # Bold text
            # Centered or low indentation
            if line.is_bold or line.indentation < 50:
                return True

        return False

    def _extract_rule_number(self, content: str) -> Optional[str]:
        """Extract rule number from content"""
        # Try regex first
        match = re.search(r'Rule\s+([0-9A-Z]+)', content, re.IGNORECASE)
        if match:
            return match.group(1)

        # Fallback to Gemini
        return self.gemini.extract_rule_number(content)

    def handle_page_continuations(
        self,
        rules: List[Rule],
        text_lines: List[TextLine]
    ) -> List[Rule]:
        """
        Handle rules that continue across page boundaries

        Args:
            rules: List of rules
            text_lines: Original text lines

        Returns:
            Rules with continuations resolved
        """
        logger.info(f"Handling page continuations for {len(rules)} rules")

        resolved_rules = []

        for i, rule in enumerate(rules):
            # Check if rule ends near page bottom
            if self._ends_near_page_bottom(rule, text_lines):
                # Get next page content
                next_page_content = self._get_next_page_start(
                    rule.end_page,
                    text_lines
                )

                if next_page_content:
                    # Use Gemini to determine if continues
                    current_end = rule.content[-500:] if len(rule.content) > 500 else rule.content
                    analysis = self.gemini.analyze_continuation(
                        current_end,
                        next_page_content,
                        context_type="rule"
                    )

                    if analysis.get('continues') and analysis.get('confidence', 0) > 0.7:
                        logger.debug(f"Rule {rule.display_number} continues to next page")
                        # Continuation handled by next rule merge
                        # For now, just log

            resolved_rules.append(rule)

        return resolved_rules

    def _ends_near_page_bottom(self, rule: Rule, text_lines: List[TextLine]) -> bool:
        """Check if rule ends near bottom of page"""
        # Find last line of rule
        rule_lines = [
            line for line in text_lines
            if line.page_number == rule.end_page
        ]

        if not rule_lines:
            return False

        # Get last line y-position
        last_line = max(rule_lines, key=lambda l: l.y)

        # Check if in bottom 15% of page
        # Assume page height ~800 (can be refined)
        page_height = 800
        bottom_threshold = page_height * (1 - self.continuation_threshold)

        return last_line.y > bottom_threshold

    def _get_next_page_start(
        self,
        current_page: int,
        text_lines: List[TextLine],
        num_lines: int = 10
    ) -> str:
        """Get first N lines of next page"""
        next_page_lines = [
            line for line in text_lines
            if line.page_number == current_page + 1
        ][:num_lines]

        return "\n".join(line.content for line in next_page_lines)

    def build_rule_hierarchy(self, rules: List[Rule]) -> List[Rule]:
        """
        Build hierarchical structure of rules (rules -> sub-rules -> clauses)

        Args:
            rules: Flat list of rules

        Returns:
            Hierarchical list of rules
        """
        logger.info(f"Building hierarchy for {len(rules)} rules")

        # For now, return flat list
        # TODO: Implement hierarchy detection based on numbering patterns
        # e.g., Rule 22 -> Rule 22(1) -> Rule 22(1)(a)

        return rules

"""
Module 6: Validator and Output Generator - Validation component
"""
from typing import List, Dict, Any, Optional
from Levenshtein import distance as levenshtein_distance

from src.models.document import Rule, ValidationResult
from src.modules.module5_consolidator.rule_tree import RuleTree
from src.utils.logger import get_logger
from src.utils.config_loader import get_config


logger = get_logger("validator")


class RulebookValidator:
    """
    Validates consolidated rulebook against reference documents
    """

    def __init__(self):
        """Initialize validator"""
        self.config = get_config()

        self.structural_threshold = self.config.get(
            'validation.structural_match_threshold',
            0.95
        )
        self.content_threshold = self.config.get(
            'validation.content_fidelity_threshold',
            0.95
        )
        self.levenshtein_threshold = self.config.get(
            'validation.levenshtein_threshold',
            0.05
        )

    def validate(
        self,
        consolidated_tree: RuleTree,
        reference_rules: Optional[List[Rule]] = None
    ) -> ValidationResult:
        """
        Validate consolidated rulebook

        Args:
            consolidated_tree: Consolidated rule tree
            reference_rules: Optional reference rules for comparison

        Returns:
            ValidationResult
        """
        logger.info("Starting validation...")

        result = ValidationResult()

        # Get consolidated rules
        consolidated_rules = consolidated_tree.get_all_rules()

        # Internal consistency checks
        internal_checks = self._check_internal_consistency(consolidated_rules)
        result.details['internal_checks'] = internal_checks

        # Cross-document validation if reference provided
        if reference_rules:
            cross_checks = self._cross_document_validation(
                consolidated_rules,
                reference_rules
            )

            result.structural_match_score = cross_checks['structural_score']
            result.content_fidelity_score = cross_checks['content_score']
            result.rule_alignment_percentage = cross_checks['alignment_percentage']
            result.anomalies = cross_checks['anomalies']
            result.details['cross_checks'] = cross_checks

            # Determine if passed
            result.passed = (
                result.structural_match_score >= self.structural_threshold and
                result.content_fidelity_score >= self.content_threshold
            )

        else:
            # Without reference, only internal validation
            result.passed = internal_checks['passed']
            result.anomalies = internal_checks['anomalies']

        logger.info(f"Validation complete: {'PASSED' if result.passed else 'FAILED'}")
        return result

    def _check_internal_consistency(
        self,
        rules: List
    ) -> Dict[str, Any]:
        """Check internal consistency of consolidated rulebook"""
        logger.info("Checking internal consistency...")

        anomalies = []

        # Check for empty rules
        empty_rules = [r for r in rules if not r.content.strip()]
        if empty_rules:
            anomalies.append(f"Found {len(empty_rules)} empty rules")

        # Check for duplicate rule numbers
        rule_numbers = [r.display_number for r in rules]
        duplicates = [num for num in rule_numbers if rule_numbers.count(num) > 1]
        if duplicates:
            unique_dups = set(duplicates)
            anomalies.append(f"Found duplicate rule numbers: {', '.join(unique_dups)}")

        # Check for numbering gaps (for main rules)
        main_rules = [r for r in rules if r.level == 0]
        main_numbers = []
        for r in main_rules:
            try:
                # Extract numeric part
                import re
                match = re.match(r'(\d+)', r.display_number)
                if match:
                    main_numbers.append(int(match.group(1)))
            except:
                pass

        if main_numbers:
            main_numbers.sort()
            expected = list(range(main_numbers[0], main_numbers[-1] + 1))
            missing = set(expected) - set(main_numbers)
            if missing:
                anomalies.append(f"Numbering gaps in main rules: {sorted(missing)}")

        passed = len(anomalies) == 0

        return {
            'passed': passed,
            'total_rules': len(rules),
            'empty_rules': len(empty_rules),
            'duplicate_numbers': len(set(duplicates)),
            'anomalies': anomalies
        }

    def _cross_document_validation(
        self,
        consolidated_rules: List,
        reference_rules: List[Rule]
    ) -> Dict[str, Any]:
        """Cross-validate against reference document"""
        logger.info("Cross-validating against reference document...")

        # Build mappings
        consolidated_map = {r.display_number: r for r in consolidated_rules}
        reference_map = {r.display_number: r for r in reference_rules}

        # Structural matching
        consolidated_numbers = set(consolidated_map.keys())
        reference_numbers = set(reference_map.keys())

        common_numbers = consolidated_numbers & reference_numbers
        alignment_percentage = len(common_numbers) / len(reference_numbers) if reference_numbers else 0

        structural_score = alignment_percentage

        # Content fidelity for common rules
        content_scores = []
        anomalies = []

        for rule_num in common_numbers:
            cons_rule = consolidated_map[rule_num]
            ref_rule = reference_map[rule_num]

            # Calculate content similarity
            similarity = self._calculate_similarity(
                cons_rule.content,
                ref_rule.content
            )
            content_scores.append(similarity)

            # Flag significant differences
            if similarity < (1.0 - self.levenshtein_threshold):
                anomalies.append(
                    f"Rule {rule_num}: Content differs significantly "
                    f"(similarity: {similarity:.2%})"
                )

        content_score = sum(content_scores) / len(content_scores) if content_scores else 0.0

        # Rules in reference but not consolidated
        missing_rules = reference_numbers - consolidated_numbers
        if missing_rules:
            anomalies.append(
                f"Missing rules from reference: {', '.join(sorted(missing_rules))}"
            )

        # Rules in consolidated but not reference
        extra_rules = consolidated_numbers - reference_numbers
        if extra_rules:
            anomalies.append(
                f"Extra rules not in reference: {', '.join(sorted(extra_rules))}"
            )

        return {
            'structural_score': structural_score,
            'content_score': content_score,
            'alignment_percentage': alignment_percentage,
            'common_rules': len(common_numbers),
            'missing_rules': len(missing_rules),
            'extra_rules': len(extra_rules),
            'anomalies': anomalies
        }

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using Levenshtein distance"""
        if not text1 and not text2:
            return 1.0

        max_len = max(len(text1), len(text2))
        if max_len == 0:
            return 1.0

        dist = levenshtein_distance(text1, text2)
        similarity = 1.0 - (dist / max_len)

        return max(0.0, min(1.0, similarity))

    def generate_audit_report(
        self,
        validation_result: ValidationResult,
        consolidated_tree: RuleTree,
        amendments_applied: int
    ) -> Dict[str, Any]:
        """
        Generate audit report

        Args:
            validation_result: Validation result
            consolidated_tree: Consolidated tree
            amendments_applied: Number of amendments applied

        Returns:
            Audit report dictionary
        """
        logger.info("Generating audit report...")

        all_rules = consolidated_tree.get_all_rules()

        # Count amendments by type
        amendment_stats = {
            'total': 0,
            'by_action': {}
        }

        for rule in all_rules:
            for amendment in rule.amendment_history:
                amendment_stats['total'] += 1
                action = amendment.action.value
                amendment_stats['by_action'][action] = \
                    amendment_stats['by_action'].get(action, 0) + 1

        report = {
            'summary': {
                'total_rules': len(all_rules),
                'amendments_applied': amendments_applied,
                'validation_status': 'PASSED' if validation_result.passed else 'FAILED'
            },
            'validation': {
                'structural_match': validation_result.structural_match_score,
                'content_fidelity': validation_result.content_fidelity_score,
                'alignment_percentage': validation_result.rule_alignment_percentage
            },
            'amendments': amendment_stats,
            'anomalies': validation_result.anomalies,
            'details': validation_result.details
        }

        return report

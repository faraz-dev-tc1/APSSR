"""
Google ADK Agent for amendment extraction
"""
import json
from typing import Dict, Any, List, Optional
from src.modules.module2_reconstructor.gemini_client import GeminiClient
from src.utils.logger import get_logger


logger = get_logger("adk_agent")


class AmendmentExtractionAgent:
    """
    ADK-style agent for intelligent amendment extraction
    Uses Gemini for understanding complex amendment instructions
    """

    def __init__(self):
        """Initialize amendment extraction agent"""
        self.gemini = GeminiClient()

    def extract_amendments_from_go(
        self,
        go_content: str,
        go_id: str,
        go_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract structured amendments from GO content

        Args:
            go_content: GO text content
            go_id: GO identifier
            go_date: GO date (ISO format)

        Returns:
            List of structured amendment objects
        """
        logger.info(f"Extracting amendments from {go_id}")

        system_instruction = """You are an expert at extracting structured amendments from Government Orders.

Your task is to:
1. Identify all amendment clauses in the GO text
2. Classify each amendment action (SUBSTITUTE, OMIT, INSERT, RENUMBER)
3. Extract target rule/sub-rule/clause references
4. Extract old and new text content
5. Return structured JSON

Amendment Actions:
- SUBSTITUTE: Replacing existing text with new text
- OMIT: Removing/deleting text
- INSERT: Adding new text
- RENUMBER: Changing numbering of rules

Focus on normative amendment instructions, not preambles or signatures."""

        prompt = f"""Extract all amendments from this Government Order:

GO ID: {go_id}
GO Date: {go_date or 'Unknown'}

GO CONTENT:
{go_content}

For each amendment, extract:
1. action: SUBSTITUTE/OMIT/INSERT/RENUMBER
2. target_path: List of hierarchical references (e.g., ["rule-22", "sub-rule-2", "clause-e"])
3. old_text: Text being replaced (if SUBSTITUTE)
4. new_text: Replacement or inserted text (if SUBSTITUTE/INSERT)
5. position: "before"/"after"/"replace" (if INSERT)
6. confidence: Your confidence in extraction (0.0-1.0)
7. context: Relevant surrounding text for reference

Return JSON array of amendments:
[
  {{
    "action": "SUBSTITUTE",
    "target_path": ["rule-22", "sub-rule-2", "clause-e"],
    "old_text": "...",
    "new_text": "...",
    "confidence": 0.95,
    "context": "..."
  }},
  ...
]

If no clear amendments found, return empty array: []
"""

        try:
            response = self.gemini.generate(prompt, system_instruction)

            # Parse JSON response
            amendments = self._parse_json_response(response)

            logger.info(f"Extracted {len(amendments)} amendments from {go_id}")
            return amendments

        except Exception as e:
            logger.error(f"Error extracting amendments from {go_id}: {str(e)}")
            return []

    def _parse_json_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse JSON from Gemini response"""
        try:
            # Clean response
            json_text = response.strip()

            # Remove markdown code blocks
            if '```' in json_text:
                parts = json_text.split('```')
                for part in parts:
                    part = part.strip()
                    if part.startswith('json'):
                        part = part[4:].strip()
                    if part.startswith('[') or part.startswith('{'):
                        json_text = part
                        break

            # Parse JSON
            data = json.loads(json_text)

            # Ensure it's a list
            if isinstance(data, dict):
                data = [data]

            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.debug(f"Response: {response[:500]}")
            return []

    def resolve_ambiguous_target(
        self,
        target_reference: str,
        context: str,
        available_rules: List[str]
    ) -> Optional[List[str]]:
        """
        Resolve ambiguous target references using context

        Args:
            target_reference: Ambiguous reference (e.g., "the said rule")
            context: Surrounding text
            available_rules: List of available rule numbers

        Returns:
            Resolved target path or None
        """
        system_instruction = """You are an expert at resolving ambiguous references in legal documents.
Given an ambiguous reference, context, and available rules, determine the specific rule being referenced."""

        prompt = f"""Resolve this ambiguous reference:

Reference: {target_reference}
Context: {context}
Available Rules: {', '.join(available_rules)}

Return the specific rule number being referenced, or "UNKNOWN" if cannot determine.
Example responses: "Rule 22", "Rule 7A", "UNKNOWN"
"""

        try:
            response = self.gemini.generate(prompt, system_instruction)
            rule_ref = response.strip().strip('"\'')

            if rule_ref.upper() == "UNKNOWN":
                return None

            # Parse into target path
            return self._parse_rule_reference(rule_ref)

        except Exception as e:
            logger.error(f"Error resolving ambiguous target: {str(e)}")
            return None

    def _parse_rule_reference(self, reference: str) -> List[str]:
        """
        Parse rule reference into hierarchical path

        Args:
            reference: Rule reference (e.g., "Rule 22(2)(e)")

        Returns:
            Hierarchical path list
        """
        import re

        path = []

        # Extract main rule
        rule_match = re.search(r'Rule\s+([0-9A-Z]+)', reference, re.IGNORECASE)
        if rule_match:
            path.append(f"rule-{rule_match.group(1)}")

        # Extract sub-rule
        subrule_match = re.search(r'\((\d+)\)', reference)
        if subrule_match:
            path.append(f"sub-rule-{subrule_match.group(1)}")

        # Extract clause
        clause_match = re.search(r'\(([a-z])\)', reference, re.IGNORECASE)
        if clause_match:
            path.append(f"clause-{clause_match.group(1).lower()}")

        return path

    def validate_amendment(
        self,
        amendment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate extracted amendment and flag issues

        Args:
            amendment: Amendment dictionary

        Returns:
            Validated amendment with flags
        """
        flagged = False
        flag_reasons = []

        # Check confidence
        confidence = amendment.get('confidence', 1.0)
        if confidence < 0.7:
            flagged = True
            flag_reasons.append(f"Low confidence: {confidence:.2f}")

        # Check target path
        target_path = amendment.get('target_path', [])
        if not target_path:
            flagged = True
            flag_reasons.append("Missing target path")

        # Check action-specific requirements
        action = amendment.get('action', '')

        if action == 'SUBSTITUTE':
            if not amendment.get('old_text') or not amendment.get('new_text'):
                flagged = True
                flag_reasons.append("SUBSTITUTE missing old_text or new_text")

        elif action == 'INSERT':
            if not amendment.get('new_text'):
                flagged = True
                flag_reasons.append("INSERT missing new_text")
            if not amendment.get('position'):
                flagged = True
                flag_reasons.append("INSERT missing position")

        elif action == 'OMIT':
            if not amendment.get('old_text'):
                flagged = True
                flag_reasons.append("OMIT missing old_text")

        # Add validation results
        amendment['flagged'] = flagged
        amendment['flag_reasons'] = flag_reasons

        if flagged:
            logger.warning(f"Flagged amendment: {', '.join(flag_reasons)}")

        return amendment

"""
Gemini API client for intelligent text analysis
"""
import os
import google.generativeai as genai
from typing import Dict, Any, Optional
from src.utils.logger import get_logger
from src.utils.config_loader import get_config


logger = get_logger("gemini_client")


class GeminiClient:
    """Client for interacting with Gemini API"""

    def __init__(self):
        """Initialize Gemini client"""
        self.config = get_config()

        # Get API key
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")

        # Configure Gemini
        genai.configure(api_key=api_key)

        # Get model configuration
        model_name = self.config.get('gemini.model', 'gemini-2.0-flash-exp')
        temperature = self.config.get('gemini.temperature', 0.1)
        max_tokens = self.config.get('gemini.max_tokens', 8000)

        # Initialize model
        generation_config = {
            'temperature': temperature,
            'max_output_tokens': max_tokens,
            'top_p': self.config.get('gemini.top_p', 0.95),
            'top_k': self.config.get('gemini.top_k', 40),
        }

        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config
        )

        logger.info(f"Initialized Gemini client with model: {model_name}")

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Generate text using Gemini

        Args:
            prompt: User prompt
            system_instruction: Optional system instruction

        Returns:
            Generated text
        """
        try:
            # Create chat session
            chat = self.model.start_chat(history=[])

            # Add system instruction if provided
            if system_instruction:
                full_prompt = f"{system_instruction}\n\n{prompt}"
            else:
                full_prompt = prompt

            # Generate response
            response = chat.send_message(full_prompt)

            return response.text

        except Exception as e:
            logger.error(f"Error generating with Gemini: {str(e)}")
            raise

    def analyze_continuation(
        self,
        current_content: str,
        next_page_content: str,
        context_type: str = "rule"
    ) -> Dict[str, Any]:
        """
        Analyze if content continues across pages

        Args:
            current_content: Content from current page
            next_page_content: Content from next page
            context_type: Type of content (rule, go, etc.)

        Returns:
            Analysis result with continuation decision
        """
        system_instruction = f"""You are an expert at analyzing legal documents.
Your task is to determine if text continues from one page to another.
Focus on {context_type} content."""

        prompt = f"""Analyze if the following text continues across pages:

CURRENT PAGE END:
{current_content}

NEXT PAGE START:
{next_page_content}

Determine:
1. Does the content continue? (yes/no)
2. Confidence level (0.0-1.0)
3. Reason for decision

Respond in JSON format:
{{
    "continues": true/false,
    "confidence": 0.0-1.0,
    "reason": "explanation"
}}
"""

        try:
            response = self.generate(prompt, system_instruction)

            # Parse JSON response
            import json
            # Extract JSON from response (handle markdown code blocks)
            json_text = response.strip()
            if json_text.startswith('```'):
                json_text = json_text.split('```')[1]
                if json_text.startswith('json'):
                    json_text = json_text[4:]
            json_text = json_text.strip()

            result = json.loads(json_text)
            return result

        except Exception as e:
            logger.error(f"Error analyzing continuation: {str(e)}")
            # Return safe default
            return {
                "continues": False,
                "confidence": 0.0,
                "reason": f"Error: {str(e)}"
            }

    def classify_content_type(self, content: str) -> Dict[str, Any]:
        """
        Classify the type of content

        Args:
            content: Text content to classify

        Returns:
            Classification result
        """
        system_instruction = """You are an expert at classifying legal document content.
Classify content as: RULE, GO (Government Order), HEADER, FOOTER, or OTHER."""

        prompt = f"""Classify the following content:

CONTENT:
{content[:500]}

Respond in JSON format:
{{
    "type": "RULE/GO/HEADER/FOOTER/OTHER",
    "confidence": 0.0-1.0,
    "details": "any relevant details"
}}
"""

        try:
            response = self.generate(prompt, system_instruction)

            # Parse JSON response
            import json
            json_text = response.strip()
            if json_text.startswith('```'):
                json_text = json_text.split('```')[1]
                if json_text.startswith('json'):
                    json_text = json_text[4:]
            json_text = json_text.strip()

            result = json.loads(json_text)
            return result

        except Exception as e:
            logger.error(f"Error classifying content: {str(e)}")
            return {
                "type": "OTHER",
                "confidence": 0.0,
                "details": f"Error: {str(e)}"
            }

    def extract_rule_number(self, content: str) -> Optional[str]:
        """
        Extract rule number from content

        Args:
            content: Text content

        Returns:
            Rule number or None
        """
        system_instruction = """You are an expert at extracting rule numbers from legal documents.
Extract the rule number if present."""

        prompt = f"""Extract the rule number from this content:

CONTENT:
{content[:300]}

Respond with just the rule number (e.g., "5", "22", "7A") or "NONE" if no rule number found.
"""

        try:
            response = self.generate(prompt, system_instruction)
            rule_num = response.strip().strip('"\'')

            if rule_num.upper() == "NONE":
                return None

            return rule_num

        except Exception as e:
            logger.error(f"Error extracting rule number: {str(e)}")
            return None
